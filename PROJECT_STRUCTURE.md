# Project Structure

```text
enterprise_ai/
├── backend/
│   ├── main.py
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── database.py
│   │   ├── services.py
│   │   ├── utils.py
│   │   ├── kb_index.py
│   │   ├── dependencies.py
│   │   ├── auth.py
│   │   └── llm/
│   ├── requirements.txt
│   ├── .env.example
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── App.vue
│   │   ├── api.js
│   │   ├── auth.js
│   │   ├── app-state.js
│   │   ├── components/
│   │   └── main.js
│   ├── tests/
│   ├── package.json
│   └── vite.config.js
├── scripts/
│   ├── smoke_check.py
│   └── package_release.sh
├── README.md
├── QUICK_START.md
├── DELIVERY_CHECKLIST.md
├── start_backend.sh
└── start_frontend.sh
```
