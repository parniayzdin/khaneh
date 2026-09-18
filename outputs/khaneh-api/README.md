# Khaneh Go API

Requires Go 1.22+. Uses only the standard library.

```bash
cd /mnt/c/Users/Parnia/Documents/Codex/2026-09-17/ok/outputs/khaneh-api
go test ./...
go run .
```

Open http://localhost:8082/ for the route list.

- GET /health: readiness and record count
- GET /api/people: all memorial records
- GET /api/people/{id}: one record or 404

Unsupported writes return 405. GET routes also support HEAD. CORS permits localhost:4173 and 127.0.0.1:4173; it is not authentication.

Records are validated and loaded from `../khaneh-portraits/assets/portraits/records.json` at startup. Restart after edits. Set `KHANEH_RECORDS_PATH` to an absolute path to run elsewhere. `KHANEH_API_ADDR` overrides the default `127.0.0.1:8082`.

The map fetches this API and offers Retry if unavailable. Start its separate frontend with `node scripts/preview.cjs` from the repository root. The Java rendering backend remains saved separately. Records still use JSON, not PostgreSQL.

Go forwards `GET /api/ask`, `GET /api/search`, and `GET /api/ai/health` to the Python AI service on port 8001. Set `KHANEH_AI_URL` to override that address. AI failures return a clear error without affecting the map. See [AI setup](../khaneh-search/README.md) for WSL commands and supported questions.
