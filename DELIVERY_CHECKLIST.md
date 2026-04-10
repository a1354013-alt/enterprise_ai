# Delivery Checklist

## Pre-delivery cleanup

- Remove `backend/.env`
- Remove `backend/*.db`
- Remove `backend/chroma_db/`
- Remove `backend/uploads/`
- Remove `frontend/node_modules/`
- Remove `frontend/dist/`
- Remove tar/zip backups
- Remove nested duplicate source trees

## Verification

- `cd backend && python tests/run_smoke.py`
- `cd frontend && npm test`
- `cd frontend && npm run build`
- Start backend on `8000`
- Start frontend on `5173`
- Login with admin account
- Verify `/api/me`
- Upload a document and confirm it is pending
- Approve the document in admin console
- Verify normal user can only see approved/active documents allowed for their role

## Packaging rule

Deliver only:

- `backend/`
- `frontend/`
- root documentation and startup scripts
- `scripts/smoke_check.py`

