# Changelog

## 5.0.0

### Product
- Knowledge + logbook entries support `status`, `source_type`, `source_ref`, and `related_item_ids` end-to-end (backend + frontend).
- Related items panel shows relationship list (traceable source chain).
- Home/landing tab shows a unified “Recent activity” timeline.

### Knowledge Link Graph
- `item_links` can be replaced on update (not append-only) to keep relationships consistent over time.
- Added link resolution endpoints: `GET /api/item-links?item_id=...` and `POST /api/items/resolve`.

### AutoTest
- AutoTest detects real project root after zip extraction and runs in the detected `working_directory`.
- AutoTest returns `execution_mode`, `project_type_detected`, and `working_directory`.
- AutoTest step logs capture command output and exit code (traceable per step).

### Documents & Photos
- Documents: download/preview endpoint and frontend metadata update/archive/delete UI.
- Photos: PATCH/DELETE + download/preview endpoints and frontend edit/delete UI.
- Documents/photos can show backlinks via related-items panel.

### Session
- Frontend clears token and redirects to login on any authenticated API `401` (except `/api/login`).

### Quality & Delivery
- Frontend interaction-level tests via Vitest.
- Backend refactored into a stable package (`backend/app/...`) with consistent imports for pytest and production.
- Added `VERSION` as a single version source and a consistency check script.
- Expanded `scripts/smoke_check.py` to cover full Knowledge Workspace workflow.
- Added GitHub Actions CI (backend pytest, frontend test/build, packaging exclusions, smoke check).

