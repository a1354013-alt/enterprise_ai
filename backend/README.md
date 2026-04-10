# Backend API

## Start

```bash
cd backend
python -m pip install -r requirements.txt
cp .env.example .env
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Main endpoints

- `POST /api/login`
- `GET /api/me`
- `POST /api/docs/upload`
- `GET /api/docs`
- `DELETE /api/docs/{doc_id}`
- `POST /api/qa`
- `POST /api/generate`
- `GET /api/admin/users`
- `POST /api/admin/users`
- `PATCH /api/admin/users/{user_id}`
- `GET /api/admin/docs`
- `PATCH /api/admin/docs/{doc_id}`
- `DELETE /api/admin/docs/{doc_id}`

## Contract rules

- Login, QA, generate, admin user create/update, and admin document update use JSON bodies
- File upload uses multipart form data
- Auth is handled only through bearer token dependency injection
- Admin authorization is centralized in `dependencies.get_current_admin`

## Tests

```bash
cd backend
python tests/run_smoke.py
```

