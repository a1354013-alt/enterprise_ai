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

- `cd backend && python -m pytest`
- `cd frontend && npm test`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`
- Start backend on `8000`
- Start frontend on `5173`
- Login with `owner` account
- Verify `/health` and `/api/health` return 200 with the same payload
- Verify `/api/me`
- Upload a document and confirm it appears in Documents list with `status=reviewed`, can be previewed/downloaded, and can be archived/deleted
- Upload a photo and confirm it appears in Photos list, can be previewed/downloaded, and can be deleted
- Create a logbook entry, promote it to knowledge, and confirm it is searchable via QA (traceable sources)
- Run AutoTest with `AUTOTEST_MODE=simulated` and confirm response includes `execution_mode`, `project_type_detected`, `working_directory`
- Confirm each knowledge/logbook entry can edit `status`, `source_type`, `source_ref`, and `related_item_ids` and shows a related-items panel

## Packaging rule

Deliver only:

- `backend/`
- `frontend/`
- root documentation and startup scripts
- `scripts/smoke_check.py`

Recommended (reproducible) packaging:

- `python scripts/package_release.py ./knowledge_workspace_release.zip`
