# Personal AI Knowledge Workspace for Engineers

Version: see `VERSION`.

Local-first workspace for **knowledge capture + traceable retrieval**:

- Knowledge entries (draft → reviewed → verified → archived)
- Troubleshooting logbook (and one-click promote to verified solutions)
- Document & screenshot/image indexing
- AI retrieval Q&A with source snippets
- AutoTest runs that automatically generate problem drafts and fix suggestions

This is intentionally **not** an ERP-style approval system and not just a file organizer.

## Quick start

1) Backend

```bash
cd backend
python -m pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

2) Frontend

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

3) Open `http://localhost:5173`

Default account:

- User ID: `owner`
- Password: the value of `DEFAULT_OWNER_PASSWORD` in `backend/.env`

## Key API endpoints

- `POST /api/login`, `GET /api/me`
- `POST /api/docs/upload`, `GET /api/docs`, `PATCH /api/docs/{doc_id}`, `DELETE /api/docs/{doc_id}`
- `GET /api/docs/{doc_id}/download`
- `GET /api/knowledge/entries`, `POST /api/knowledge/entries`, `PATCH /api/knowledge/entries/{entry_id}`
- `GET /api/logbook/entries`, `POST /api/logbook/entries`, `PATCH /api/logbook/entries/{entry_id}`, `POST /api/logbook/entries/{entry_id}/promote-to-knowledge`
- `POST /api/autotest/run`, `GET /api/autotest/runs`, `GET /api/autotest/runs/{run_id}`
- `POST /api/qa`, `GET /api/meta/templates`, `POST /api/generate`
- `GET /api/item-links?item_id=...`, `POST /api/items/resolve`

## Validation

```bash
cd backend
python -m pytest
```

```bash
cd frontend
npm test
```

```bash
python scripts/smoke_check.py --password "<owner password>"
```
