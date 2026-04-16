# Changelog v4.2 (Workflow Workbench Hardening)

This release focused on collapsing the app into a single, verifiable workflow workbench:

Knowledge → Logbook → AutoTest → Prompt → Knowledge (feedback loop)

Note: newer releases (e.g. `5.0.0`) further changed session/401 policy and backend structure; treat this file as historical context for `v4.2` only.

## Highlights

- Canonical frontend path is `frontend/` (removed legacy `frontend-vue/` references).
- Token storage is single-source-of-truth: `localStorage` via `frontend/src/auth.js`.
- AutoTest workflow is end-to-end:
  - Backend implements `/api/autotest/run`, `/api/autotest/runs`, `/api/autotest/runs/{id}`.
  - Failed runs auto-create a Logbook entry and link it to the run.
  - Passed runs auto-create a Knowledge candidate (`status=draft`) for human review.

## Files of note (as of v4.2)

- `frontend/src/api.js` - axios client + auth error policy
- `frontend/src/auth.js` - token lifecycle + unauthorized event
- `frontend/src/components/AutoTestPanel.vue` - UI for acceptance runs
- `backend/main.py` - FastAPI routes + error handling (since `5.0.0`, this is a compatibility wrapper for `backend/app/main.py`)
- `backend/database.py` - persistence layer (since `5.0.0`, this lives in `backend/app/database.py`)

