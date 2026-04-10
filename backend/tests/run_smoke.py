from __future__ import annotations

import importlib
import os
import sys
import uuid
from pathlib import Path

from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).resolve().parents[1]


def load_app():
    run_id = uuid.uuid4().hex
    os.environ['JWT_SECRET'] = 'smoke-secret'
    os.environ['DEFAULT_ADMIN_PASSWORD'] = 'AdminPass123!'
    os.environ['DATABASE_PATH'] = ':memory:'
    os.environ['UPLOAD_DIR'] = f'uploads_smoke_{run_id}'
    os.environ['CHROMA_DB_PATH'] = f'chroma_smoke_{run_id}'
    os.environ['ALLOWED_ORIGINS'] = 'http://localhost:5173'

    for module_name in ['models', 'auth', 'utils', 'database', 'dependencies', 'services', 'main']:
        if module_name in sys.modules:
            del sys.modules[module_name]

    main = importlib.import_module('main')
    main.delete_from_vector_db = lambda doc_id: True

    def fake_process_file(doc_id, file_path, filename, allowed_roles, approved=1, is_active=1):
        return doc_id

    async def fake_perform_qa(question, user_role):
        return (f'answer for {user_role}', [])

    main.process_file = fake_process_file
    main.perform_qa = fake_perform_qa
    return main


def auth_headers(client, user_id='admin', password='AdminPass123!'):
    response = client.post('/api/login', json={'user_id': user_id, 'password': password})
    assert response.status_code == 200, response.text
    token = response.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def main() -> int:
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))

    app_module = load_app()
    client = TestClient(app_module.app)

    ok = client.post('/api/login', json={'user_id': 'admin', 'password': 'AdminPass123!'})
    bad = client.post('/api/login', json={'user_id': 'admin', 'password': 'wrong-pass'})
    assert ok.status_code == 200
    assert bad.status_code == 401
    print('PASS login success/failure')

    admin_headers = auth_headers(client)
    me = client.get('/api/me', headers=admin_headers)
    assert me.status_code == 200 and me.json()['user_id'] == 'admin'
    print('PASS /api/me')

    create_user = client.post('/api/admin/users', headers=admin_headers, json={
        'user_id': 'employee1',
        'password': 'Employee123!',
        'display_name': 'Employee One',
        'role': 'employee',
        'is_active': 1,
    })
    assert create_user.status_code == 200, create_user.text
    print('PASS admin user create')

    app_module.db.add_document('doc-approved', 'approved.txt', 'approved.txt', ['employee'], 10, 'admin')
    app_module.db.update_document('doc-approved', approved=1, is_active=1, allowed_roles=['employee'])
    app_module.db.add_document('doc-pending', 'pending.txt', 'pending.txt', ['employee'], 10, 'admin')
    employee_headers = auth_headers(client, 'employee1', 'Employee123!')
    docs = client.get('/api/docs', headers=employee_headers)
    assert docs.status_code == 200
    assert [doc['id'] for doc in docs.json()] == ['doc-approved']
    print('PASS document permission filter')

    uploads_dir = Path(app_module.UPLOAD_DIR)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    (uploads_dir / 'manual.txt').write_text('content', encoding='utf-8')
    app_module.db.add_document('doc-admin', 'manual.txt', 'manual.txt', ['manager'], 10, 'admin')
    update_doc = client.patch('/api/admin/docs/doc-admin', headers=admin_headers, json={
        'allowed_roles': ['manager'],
        'approved': 1,
        'is_active': 1,
    })
    assert update_doc.status_code == 200, update_doc.text
    delete_doc = client.delete('/api/admin/docs/doc-admin', headers=admin_headers)
    assert delete_doc.status_code == 200, delete_doc.text
    print('PASS admin doc update/delete')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

