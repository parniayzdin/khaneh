# Khaneh measurements

This benchmark measures the existing memorial atlas: JavaScript frontend, Go API, Python/FastAPI, Sentence Transformers and PyTorch. It does not measure a home-management application, production traffic, or real-user time savings.

## Run in WSL

Start Go on 8082 and Python on 8001 as described in `outputs/khaneh-search/README.md`. From the repository root:

```bash
cd /mnt/c/Users/Parnia/Documents/Codex/2026-09-17/ok
python3 benchmarks/measure.py
```

No additional Python packages are required for the benchmark client. The command runs:

1. Five excluded warm-up GET requests, then 500 requests to `/api/people` using 10 concurrent worker threads. Each response must contain exactly the expected nine IDs.
2. Twelve hand-labeled retrieval queries, measuring top-1 hits, top-3 hits and mean reciprocal rank at three.
3. Sixteen answer-behavior cases: six supported, six unsupported and four ambiguous questions. Five sequential passes provide 80 latency samples. A separate distribution contains only the 30 requests with answerable questions. One model warm-up is excluded.
4. Go unit tests and statement coverage if `go` is available.

Results include raw request timings, per-question responses, failures, parameters, OS/CPU, Git revision and SHA-256 hashes of the source data, AI implementation and question set. The client opens a new HTTP connection per request. Models are already loaded; download/startup time is excluded. Run client and servers on the same WSL host to reproduce the checked-in local baseline.

For a larger experiment, use:

```bash
python3 benchmarks/measure.py --requests 5000 --concurrency 20 --repeats 10 --output benchmarks/results/experiment.json
```

The default output is `benchmarks/results/latest.json`; save a different filename before comparing runs. Keep the same CPU, service versions, question set, concurrency and warm-up procedure. Repeat at least three times before claiming a sustained speed improvement. The short requests-per-second measurement is an observed local rate, not maximum capacity.

## Baseline on 18 September 2026

Source revision: `2fcca41`; AMD Ryzen 9 5900HX, 16 logical CPUs, WSL, CPU inference. Full evidence: [results/latest.json](results/latest.json).

| Measurement | Observed result |
| --- | --- |
| People API | 500/500 valid responses, 10 concurrent workers |
| People API latency | p50 4.66 ms; p95 7.78 ms; p99 10.05 ms |
| Retrieval top-1 | 12/12 expected people ranked first |
| Answer behavior | 13/16 unique cases passed |
| Supported questions | 6/6 passed |
| Unsupported questions | 4/6 correctly abstained |
| Ambiguous questions | 3/4 correctly asked for clarification |
| Answerable-question latency | p95 133.95 ms over 30 sequential requests |
| Go statement coverage | 76.3% across the package, including startup code |

`p95` means 95% of successful measured requests completed within that duration. Failed requests are counted separately. Percentiles use nearest rank. No-answer replies still count as successful HTTP requests, so transport success must not be interpreted as answer correctness.

This is a small development set, not a held-out assessment or proof of general accuracy. Passing answer checks verifies expected status, person, required text fragments and presence of HTTPS source links. It does not independently prove that all claims are supported by those sources. Record new failures instead of changing labels to improve scores.

The baseline exposed three failures: a favorite-film question about Mani, a favorite-ice-cream question about Hadis, and the ambiguous pronoun “him.” The first two returned unrelated passages; the third selected a person without clarification. Those failed cases remain visible in the report.

## Resume wording supported by this run

**Khaneh — AI-Powered Memorial Atlas | Go, Python, FastAPI, PyTorch, JavaScript, WebGL**

- Built a Go REST API for an interactive memorial atlas, serving 500/500 valid responses at 10 concurrent clients with 7.8 ms p95 latency in local load testing.
- Integrated CPU-based semantic retrieval and extractive question answering over 19 source-linked passages, ranking the expected person first on 12/12 labeled development queries and achieving 134 ms p95 latency across 30 answerable-question requests.
- Developed a reproducible evaluation harness covering 28 labeled queries, API load testing and failure reporting; verified 76.3% Go statement coverage with automated route and upstream-error tests.

Choose two or three bullets according to the job. Do not call the second metric “100% AI accuracy.” These are synthetic local results, not production users or requests at scale. Do not add React, PostgreSQL, Docker, C#/.NET, household features, or deployment savings to this title without implementing and measuring them in this application path.

## Next measurable improvements

- Improve no-answer detection, then compare unsupported-question refusal rate on a new independently labeled set. Keep this set as a regression suite and report tuning separately from held-out results.
- Add request caching if repeated queries are a real use case; measure cold/warm p95, cache hit rate and invalidation after source edits on the same workload.
- Run a sustained load experiment with multiple concurrency levels, duration and error budgets. Current ten-worker results do not establish a supported user limit.
- For task-completion time claims, recruit users, define identical lookup tasks, measure a baseline and the new interface, and report participant count and median time. Do not infer saved time from server latency.

C#/.NET is a possible future backend implementation, not a current dependency. ASP.NET Core could implement the same Go API contract while Python remains the AI service. Benchmark both under identical conditions before making a comparative performance claim.
