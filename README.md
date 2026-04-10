# Enterprise AI Assistant 4.2.0

This repository now ships one canonical backend and one canonical frontend:

- `backend/`: FastAPI API, authentication, document metadata, vector indexing, smoke tests
- `frontend/`: Vue 3 app, unified API client, token lifecycle, admin console, frontend smoke tests

## Runtime contract

- Frontend dev server: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Auth: bearer token only, stored in one place (`localStorage`) and restored through `frontend/src/auth.js`
- Login/admin/user/document update APIs: JSON request bodies
- File upload API: multipart form with `file` and `allowed_roles`

## Quick start

1. Backend

```bash
cd backend
python -m pip install -r requirements.txt
cp .env.example .env
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

2. Frontend

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

3. Open [http://localhost:5173](http://localhost:5173)

Default admin account:

- User ID: `admin`
- Password: the value of `DEFAULT_ADMIN_PASSWORD` in `backend/.env`

## Validation

Backend smoke tests:

```bash
cd backend
python tests/run_smoke.py
```

Frontend smoke tests:

```bash
cd frontend
npm test
```

HTTP smoke check against a running backend:

```bash
python scripts/smoke_check.py --password "<admin password>"
```

## Delivery hygiene

The repo ignores and should not ship:

- `.env` files
- SQLite databases
- Chroma/vector data
- uploads
- `node_modules`
- build output
- tar/zip backups
- caches and `__pycache__`

## Current version

- App version: `4.2.0`
- Frontend package version: `4.2.0`
- Backend API version: `4.2.0`

