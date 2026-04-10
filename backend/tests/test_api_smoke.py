from __future__ import annotations

import importlib
import sys
from pathlib import Path

from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def load_app(monkeypatch, tmp_path):
    monkeypatch.setenv('JWT_SECRET', 'test-secret')
    monkeypatch.setenv('DEFAULT_ADMIN_PASSWORD', 'AdminPass123!')
    monkeypatch.setenv('DATABASE_PATH', str(tmp_path / 'test.db'))
    monkeypatch.setenv('UPLOAD_DIR', str(tmp_path / 'uploads'))
    monkeypatch.setenv('CHROMA_DB_PATH', str(tmp_path / 'chroma'))
    monkeypatch.setenv('ALLOWED_ORIGINS', 'http://localhost:5173')

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
    token = response.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def test_login_success_and_failure(monkeypatch, tmp_path):
    main = load_app(monkeypatch, tmp_path)
    client = TestClient(main.app)

    ok = client.post('/api/login', json={'user_id': 'admin', 'password': 'AdminPass123!'})
    bad = client.post('/api/login', json={'user_id': 'admin', 'password': 'wrong-pass'})

    assert ok.status_code == 200
    assert 'access_token' in ok.json()
    assert bad.status_code == 401


def test_me_endpoint(monkeypatch, tmp_path):
    main = load_app(monkeypatch, tmp_path)
    client = TestClient(main.app)

    response = client.get('/api/me', headers=auth_headers(client))

    assert response.status_code == 200
    assert response.json()['user_id'] == 'admin'


def test_document_visibility_permissions(monkeypatch, tmp_path):
    main = load_app(monkeypatch, tmp_path)
    client = TestClient(main.app)
    admin_headers = auth_headers(client)

    client.post('/api/admin/users', headers=admin_headers, json={
        'user_id': 'employee1',
        'password': 'Employee123!',
        'display_name': 'Employee One',
        'role': 'employee',
        'is_active': 1,
    })
    main.db.add_document('doc-approved', 'approved.txt', 'approved.txt', ['employee'], 10, 'admin')
    main.db.update_document('doc-approved', approved=1, is_active=1, allowed_roles=['employee'])
    main.db.add_document('doc-pending', 'pending.txt', 'pending.txt', ['employee'], 10, 'admin')

    employee_headers = auth_headers(client, 'employee1', 'Employee123!')
    response = client.get('/api/docs', headers=employee_headers)

    assert response.status_code == 200
    payload = response.json()
    assert [doc['id'] for doc in payload] == ['doc-approved']


def test_admin_crud_flow(monkeypatch, tmp_path):
    main = load_app(monkeypatch, tmp_path)
    client = TestClient(main.app)
    admin_headers = auth_headers(client)

    create_user = client.post('/api/admin/users', headers=admin_headers, json={
        'user_id': 'manager1',
        'password': 'Manager123!',
        'display_name': 'Manager One',
        'role': 'manager',
        'is_active': 1,
    })
    update_user = client.patch('/api/admin/users/manager1', headers=admin_headers, json={'display_name': 'Manager Prime'})

    uploads_dir = Path(main.UPLOAD_DIR)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    (uploads_dir / 'manual.txt').write_text('content', encoding='utf-8')
    main.db.add_document('doc-admin', 'manual.txt', 'manual.txt', ['manager'], 10, 'admin')
    update_doc = client.patch('/api/admin/docs/doc-admin', headers=admin_headers, json={
        'allowed_roles': ['manager'],
        'approved': 1,
        'is_active': 1,
    })
    delete_doc = client.delete('/api/admin/docs/doc-admin', headers=admin_headers)

    assert create_user.status_code == 200
    assert update_user.status_code == 200
    assert update_doc.status_code == 200
    assert delete_doc.status_code == 200
