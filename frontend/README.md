# Frontend Overview

This folder contains the only supported frontend delivery tree.

## Commands

```bash
npm install
npm run dev -- --host 0.0.0.0 --port 5173
npm test
npm run build
```

## Architecture

- `src/api.js`: single axios client and response handling
- `src/auth.js`: token storage, restore, clear, unauthorized event flow
- `src/app-state.js`: default app state helpers
- `src/App.vue`: login, token restore, documents, QA, templates
- `src/components/AdminConsole.vue`: admin CRUD workflows
