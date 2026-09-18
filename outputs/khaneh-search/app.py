"""Local semantic retrieval and extractive, cited question answering."""
from contextlib import asynccontextmanager
from pathlib import Path
import json
import logging
import re
from threading import Lock

import torch
from fastapi import FastAPI, HTTPException, Query
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForQuestionAnswering, AutoTokenizer

ROOT = Path(__file__).resolve().parent
RECORDS_PATH = ROOT.parent / "khaneh-portraits/assets/portraits/records.json"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
QA_MODEL = "deepset/minilm-uncased-squad2"
INFERENCE_LOCK = Lock()


def load_documents(people):
    docs = [dict(person_id=p["id"], text=f"{p['name']}. {p['story']}",
                 sources=p["sources"], kind="biography") for p in people]
    notes = json.loads((ROOT / "source_notes.json").read_text(encoding="utf-8"))
    ids = {p["id"] for p in people}
    for note in notes:
        if note["person_id"] not in ids or not note["text"] or not note["sources"]:
            raise ValueError("Invalid source note")
        if any(not s["url"].startswith("https://") for s in note["sources"]):
            raise ValueError("Source links must use HTTPS")
        docs.append(note)
    return docs


@asynccontextmanager
async def lifespan(app: FastAPI):
    torch.set_num_threads(4)
    people = json.loads(RECORDS_PATH.read_text(encoding="utf-8"))
    logging.warning("Loading CPU embedding and question-answering models; first run downloads weights.")
    model = SentenceTransformer(EMBED_MODEL, device="cpu")
    tokenizer = AutoTokenizer.from_pretrained(QA_MODEL)
    reader = AutoModelForQuestionAnswering.from_pretrained(QA_MODEL).eval()
    documents = load_documents(people)
    app.state.people = people
    app.state.documents = documents
    app.state.model = model
    app.state.tokenizer = tokenizer
    app.state.reader = reader
    app.state.embeddings = model.encode([d["text"] for d in documents], normalize_embeddings=True)
    yield


app = FastAPI(title="Khaneh AI Search & Answers", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ready", "device": "cpu", "stories": len(app.state.people),
            "passages": len(app.state.documents), "answer_mode": "extractive",
            "language": "English", "live_web_search": False}


def rank(query, person_id=""):
    embedding = app.state.model.encode(query, normalize_embeddings=True)
    scores = app.state.embeddings @ embedding
    return [(app.state.documents[int(i)], float(scores[i]))
            for i in scores.argsort()[::-1]
            if not person_id or app.state.documents[int(i)]["person_id"] == person_id]


def resolve_person(query, person_id):
    if person_id:
        if person_id not in {p["id"] for p in app.state.people}:
            raise HTTPException(404, "Person not found")
        return person_id
    matches = []
    for p in app.state.people:
        aliases = {p["id"], p["name"].split()[0].lower()}
        if p["id"] == "jina":
            aliases.add("mahsa")
        if p["id"] == "khodanoor":
            aliases.update(["khodanour", "khodanur", "khadnoor"])
        if any(re.search(r"\b" + re.escape(a) + r"\b", query.lower()) for a in aliases):
            matches.append(p["id"])
    if len(matches) > 1:
        return None
    return matches[0] if matches else ""


def read_span(question, context):
    """Choose only context tokens; compare against SQuAD2's no-answer token."""
    tokens = app.state.tokenizer(question, context, return_tensors="pt",
                                 return_offsets_mapping=True, truncation="only_second", max_length=512)
    offsets = tokens.pop("offset_mapping")[0].tolist()
    context_tokens = [i for i, seq in enumerate(tokens.sequence_ids()) if seq == 1]
    with torch.inference_mode():
        output = app.state.reader(**tokens)
    start, end = output.start_logits[0], output.end_logits[0]
    null_score = float(start[0] + end[0])
    best = (-float("inf"), 0, 0)
    for i in context_tokens:
        for j in context_tokens:
            if i <= j < i + 40:
                score = float(start[i] + end[j])
                if score > best[0]:
                    best = (score, offsets[i][0], offsets[j][1])
    return context[best[1]:best[2]], best[0] - null_score


@app.get("/search")
def search(q: str = Query(min_length=2, max_length=300), limit: int = Query(default=3, ge=1, le=9)):
    query = q.strip()
    if len(query) < 2:
        raise HTTPException(422, "Enter at least two characters")
    with INFERENCE_LOCK:
        ranked = rank(query)
    results, seen = [], set()
    for doc, score in ranked:
        if doc["person_id"] in seen:
            continue
        seen.add(doc["person_id"])
        person = next(p for p in app.state.people if p["id"] == doc["person_id"])
        results.append({k: person[k] for k in ["id", "name", "city", "story", "sources"]} |
                       {"score": round(score, 4)})
        if len(results) == limit:
            break
    return {"query": query, "results": results}


@app.get("/ask")
def ask(q: str = Query(min_length=2, max_length=300), person_id: str = Query(default="", max_length=40)):
    query = q.strip()
    if len(query) < 2:
        raise HTTPException(422, "Enter at least two characters")
    person = resolve_person(query, person_id)
    base = {"query": query, "mode": "extractive", "sources": [], "person_id": person or ""}
    if person is None or (not person and re.search(r"\b(he|she|they|his|her|their)\b", query.lower())):
        return base | {"status": "clarify", "answer": "Please choose a person or include one person's name in your question."}
    # An observed attendance date does not establish someone's first-ever protest.
    if re.search(r"\bfirst\b", query.lower()) and re.search(r"\b(protest|demonstrat)\w*", query.lower()):
        return base | {"status": "not_found", "answer": "The archive does not establish a first-ever protest date. It contains some documented attendance dates; please ask when the person was seen or reported at a protest."}
    with INFERENCE_LOCK:
        candidates = rank(query, person)[:4]
        answers = []
        for doc, similarity in candidates:
            if similarity < 0.20:
                continue
            span, margin = read_span(query, doc["text"])
            if span.strip() and margin >= 2.0:
                answers.append((margin, similarity, doc, span))
    if not answers:
        return base | {"status": "not_found", "answer": "I couldn't find a supported answer in the archive. Try a more specific question or check the person's linked sources."}
    _, _, doc, span = max(answers, key=lambda a: a[0])
    # Keep the whole short passage so attribution and uncertainty survive extraction.
    return base | {"status": "answered", "answer": doc["text"], "matched_text": span,
                   "person_id": doc["person_id"], "sources": doc["sources"],
                   "evidence_kind": doc.get("kind", "source_note")}
