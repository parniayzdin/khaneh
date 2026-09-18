# Khaneh local AI

The browser calls Go on port 8082. Go forwards `/api/ask` to Python's `/ask` on port 8001. Python retrieves passages with Sentence Transformers and uses a second model to check for an answer in those passages. Go sends the answer and citations back to the page.

## Run in WSL

From this directory, using the existing environment:

```bash
cd /mnt/c/Users/Parnia/Documents/Codex/2026-09-17/ok/outputs/khaneh-search
source .venv-wsl/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8001
```

Leave that terminal running. In another WSL terminal:

```bash
cd /mnt/c/Users/Parnia/Documents/Codex/2026-09-17/ok/outputs/khaneh-api
go run .
```

For the frontend, run `node scripts/preview.cjs` from the repository root in a terminal with Node installed. Open http://127.0.0.1:4173/ and scroll to **Ask the archive**.

For a new environment, `python3 -m venv .venv-wsl` first, activate it, and install CPU PyTorch with `python -m pip install torch --index-url https://download.pytorch.org/whl/cpu` before installing the requirements. You do not need to reinstall an already working PyTorch environment. Environments stored under `/mnt/c` can take longer to import packages than those under your WSL home directory.

## What the AI does

- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`.
- Answer reader: `deepset/minilm-uncased-squad2`, a pretrained extractive question-answering model ([model card](https://huggingface.co/deepset/minilm-uncased-squad2)). No training or fine-tuning was performed.
- Both use PyTorch on CPU. No CUDA, NVIDIA GPU, paid API, or API key is required.
- Reads the nine biographies plus ten researched, paraphrased passages in `source_notes.json`. Each note has source links and a review date. These notes add information beyond the visible biographies, but are not full copies of the articles.
- Embeds passages at startup. A question gets its own embedding; the service retrieves up to four passages, scoped to the selected or named person where possible.
- The reader scores possible answer spans against a no-answer alternative. Retrieval similarity below 0.20 or answer margin below 2.0 is rejected. These are heuristics, not calibrated confidence probabilities or guarantees of correctness.
- Returns the full supporting paragraph to retain attribution and conflicting accounts, plus source links. It does not generate new prose or combine multiple documents into a new narrative.
- Questions referring only to "he/she/they" require a name or person selection. Questions about multiple named people ask for one person at a time.
- English questions only in this version. No conversation memory, live internet browsing, or automatic source updates. Unsupported questions can be missed or incorrectly matched; users should check the cited evidence.

The first startup downloads public model weights from Hugging Face. Questions and source text are processed locally. Models are cached outside Git; subsequent inference does not need a hosted AI service. Restart Python after editing biographies or source notes. Restart Go as well after editing biographies.

## API and checks

- `GET /api/ask?q=When+did+Nika+join+the+protests%3F&person_id=nika`
- `GET /api/search?q=football&limit=3` (ranked search results, not answers)
- `GET /api/ai/health` (checks the Python service; Go's `/health` checks only Go)
- Python's interactive endpoint documentation: http://127.0.0.1:8001/docs

Run `python check_answers.py` with both servers running. This checks answers, citations, abstention, person selection, ambiguity and invalid inputs. Run `go test ./...` in `khaneh-api` for proxy routing, upstream failures, timeouts and CORS checks.

If the page says AI answers are unavailable, start Python and wait for **Application startup complete**. The map still works while AI is offline. Go waits at most 25 seconds for Python; the browser offers a new attempt after failures. `KHANEH_AI_URL` can override Go's Python service address.
