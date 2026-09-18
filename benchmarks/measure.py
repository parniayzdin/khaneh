"""Repeatable local measurements using only Python's standard library."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tempfile
import time
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent


def percentile(values, fraction):
    """Nearest-rank percentile; failed requests are reported separately."""
    return round(sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)], 2) if values else None


def timings(rows):
    good = [r['ms'] for r in rows if not r.get('error')]
    return {'requests': len(rows), 'successful': len(good), 'failed': len(rows) - len(good),
            'p50_ms': percentile(good, .50), 'p95_ms': percentile(good, .95),
            'p99_ms': percentile(good, .99)}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:8082')
    parser.add_argument('--requests', type=int, default=500)
    parser.add_argument('--concurrency', type=int, default=10)
    parser.add_argument('--repeats', type=int, default=5)
    parser.add_argument('--output', type=Path, default=ROOT / 'benchmarks/results/latest.json')
    args = parser.parse_args()
    if not (1 <= args.requests <= 10000 and 1 <= args.concurrency <= 50 and 1 <= args.repeats <= 20):
        parser.error('Use 1–10000 requests, 1–50 workers, and 1–20 repeats.')

    def request(path, **params):
        started = time.perf_counter()
        try:
            with urlopen(args.base_url.rstrip('/') + path + '?' + urlencode(params), timeout=30) as response:
                data = json.load(response)
            return {'ms': round((time.perf_counter() - started) * 1000, 3), 'data': data}
        except Exception as error:
            return {'ms': round((time.perf_counter() - started) * 1000, 3), 'error': str(error)}

    health = request('/api/ai/health')
    records = request('/api/people')
    if health.get('error') or records.get('error'):
        raise SystemExit('Start Go and Python first. ' + str(health.get('error') or records.get('error')))
    expected_ids = {p['id'] for p in records['data']}
    cases_path = ROOT / 'benchmarks/cases.json'
    cases = json.loads(cases_path.read_text())
    report = {
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'git_commit': git('rev-parse', 'HEAD'),
        'tracked_changes': git('diff', '--name-only').splitlines(),
        'environment': {'os': platform.platform(), 'python': platform.python_version(),
                        'logical_cpus': os.cpu_count(), 'client': 'Python urllib; new connection per request'},
        'settings': {'base_url': args.base_url, 'requests': args.requests,
                     'concurrency': args.concurrency, 'answer_repeats': args.repeats},
        'ai_health': health['data'],
        'scope': cases['description'],
        'hashes': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in
                   [cases_path, ROOT / 'outputs/khaneh-search/app.py', ROOT / 'outputs/khaneh-search/source_notes.json',
                    ROOT / 'outputs/khaneh-portraits/assets/portraits/records.json']},
    }
    cpuinfo = Path('/proc/cpuinfo')
    if cpuinfo.exists():
        match = re.search(r'model name\s*:\s*(.+)', cpuinfo.read_text())
        report['environment']['cpu'] = match.group(1) if match else 'unknown'

    print('Measuring people API...', flush=True)
    for _ in range(5):
        request('/api/people')  # Excluded warm-up requests.

    def people_request(_):
        row = request('/api/people')
        data = row.pop('data', None)
        if not row.get('error') and (not isinstance(data, list) or {p.get('id') for p in data} != expected_ids or len(data) != len(expected_ids)):
            row['error'] = 'Unexpected record set'
        return row

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        rows = list(pool.map(people_request, range(args.requests)))
    elapsed = time.perf_counter() - started
    report['people_api'] = timings(rows) | {'elapsed_seconds': round(elapsed, 3),
        'successful_requests_per_second': round(sum(not r.get('error') for r in rows) / elapsed, 2),
        'raw_requests': rows}

    print('Measuring retrieval...', flush=True)
    retrieval = []
    for case in cases['retrieval']:
        row = request('/api/search', q=case['q'], limit=3)
        ids = [p['id'] for p in row.get('data', {}).get('results', [])]
        rank = ids.index(case['person_id']) + 1 if case['person_id'] in ids else None
        retrieval.append(case | {'returned_ids': ids, 'rank': rank, 'ms': row['ms'], 'error': row.get('error')})
    report['retrieval'] = {'cases': len(retrieval), 'top1_correct': sum(r['rank'] == 1 for r in retrieval),
        'top3_correct': sum(r['rank'] is not None for r in retrieval),
        'mrr_at_3': round(sum(1 / r['rank'] if r['rank'] else 0 for r in retrieval) / len(retrieval), 4),
        'details': retrieval}

    print('Measuring answer behavior and latency...', flush=True)
    request('/api/ask', q=cases['answers'][0]['q'])  # Exclude model warm-up.
    answers, answer_latency = [], []
    for repeat in range(args.repeats):
        for case in cases['answers']:
            row = request('/api/ask', q=case['q'], person_id=case['person_id'])
            data = row.get('data', {})
            valid_sources = bool(data.get('sources')) and all(s.get('url', '').startswith('https://') for s in data['sources'])
            passed = (not row.get('error') and data.get('status') == case['status']
                      and data.get('person_id') == case['expected_person']
                      and all(s.lower() in data.get('answer', '').lower() for s in case['answer_contains'])
                      and (valid_sources if case['status'] == 'answered' else data.get('sources') == []))
            if repeat == 0:
                answers.append(case | {'passed': passed, 'response': data, 'error': row.get('error')})
            answer_latency.append({'ms': row['ms'], 'error': row.get('error'), 'q': case['q'],
                                   'expected_status': case['status'], 'passed': passed})
    report['answers'] = {'unique_cases': len(answers), 'passed': sum(r['passed'] for r in answers),
        'by_expected_status': {status: {'cases': sum(r['status'] == status for r in answers),
                                     'passed': sum(r['status'] == status and r['passed'] for r in answers)}
                               for status in ['answered', 'not_found', 'clarify']},
        'latency_all': timings(answer_latency),
        'latency_answerable_questions': timings([r for r in answer_latency if r['expected_status'] == 'answered']),
        'all_runs_passed': sum(r['passed'] for r in answer_latency),
        'raw_requests': answer_latency, 'details': answers}

    if shutil.which('go'):
        with tempfile.TemporaryDirectory() as directory:
            coverage = str(Path(directory) / 'coverage.out')
            tested = subprocess.run(['go', 'test', '-count=1', '-coverprofile=' + coverage, './...'],
                                    cwd=ROOT / 'outputs/khaneh-api', capture_output=True, text=True)
            report['go_tests'] = {'passed': tested.returncode == 0, 'output': tested.stdout + tested.stderr}
            if tested.returncode == 0:
                covered = subprocess.check_output(['go', 'tool', 'cover', '-func=' + coverage],
                                                  cwd=ROOT / 'outputs/khaneh-api', text=True)
                report['go_tests']['coverage_output'] = covered
                report['go_tests']['statement_coverage_percent'] = float(re.search(r'total:.*?([\d.]+)%', covered).group(1))
    else:
        report['go_tests'] = {'skipped': 'Go executable not found; run in WSL with Go installed.'}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: {a: b for a, b in report[k].items() if a not in ['raw_requests', 'details', 'coverage_output']}
                      for k in ['people_api', 'retrieval', 'answers', 'go_tests']}, indent=2))
    print('Saved', args.output)


if __name__ == '__main__':
    main()
