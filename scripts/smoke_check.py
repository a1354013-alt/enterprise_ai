from __future__ import annotations

import argparse
import json
import time
import uuid
import zipfile
from io import BytesIO
from urllib import error, request


def call(method: str, url: str, payload: dict | None = None, token: str | None = None) -> tuple[int, str]:
    data = None if payload is None else json.dumps(payload).encode('utf-8')
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=15) as response:
            return response.getcode(), response.read().decode('utf-8')
    except error.HTTPError as exc:
        return exc.code, exc.read().decode('utf-8')


def call_multipart(
    *,
    url: str,
    fields: dict[str, str] | None = None,
    file_field: str,
    filename: str,
    file_bytes: bytes,
    content_type: str,
    token: str | None = None,
) -> tuple[int, str]:
    boundary = f"----smoke-{uuid.uuid4().hex}"
    fields = fields or {}
    lines: list[bytes] = []

    def add_line(value: str) -> None:
        lines.append(value.encode("utf-8"))

    for key, value in fields.items():
        add_line(f"--{boundary}")
        add_line(f'Content-Disposition: form-data; name="{key}"')
        add_line("")
        add_line(str(value))

    add_line(f"--{boundary}")
    add_line(f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"')
    add_line(f"Content-Type: {content_type}")
    add_line("")
    lines.append(file_bytes)
    add_line(f"--{boundary}--")
    add_line("")

    body = b"\r\n".join(lines)
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = request.Request(url, data=body, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=30) as response:
            return response.getcode(), response.read().decode("utf-8")
    except error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


def build_autotest_zip_bytes() -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("package.json", '{"name":"smoke-project","version":"0.0.0"}')
        archive.writestr("README.md", "smoke check")
    return buffer.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description='Basic delivery smoke check for Personal AI Knowledge Workspace')
    parser.add_argument('--base-url', default='http://localhost:8000')
    parser.add_argument('--user-id', default='owner')
    parser.add_argument('--password', required=True)
    args = parser.parse_args()

    status_code, body = call('POST', f"{args.base_url}/api/login", {'user_id': args.user_id, 'password': args.password})
    print('LOGIN', status_code, body)
    if status_code != 200:
        return 1

    token = json.loads(body)['access_token']
    for path in ['/api/me', '/api/docs', '/api/photos', '/api/prompts']:
        code, response_body = call('GET', f'{args.base_url}{path}', token=token)
        print(path, code, response_body)
        if code != 200:
            return 1

    smoke_id = uuid.uuid4().hex[:10]
    smoke_marker = f"SMOKE_{smoke_id}"

    # Create a logbook entry
    logbook_payload = {
        "title": f"Smoke logbook {smoke_marker}",
        "problem": f"Problem {smoke_marker}",
        "root_cause": "",
        "solution": f"Solution {smoke_marker}",
        "tags": f"smoke,{smoke_marker}",
        "status": "draft",
        "source_type": "manual",
        "source_ref": "",
        "related_item_ids": [],
    }
    code, body = call("POST", f"{args.base_url}/api/logbook/entries", logbook_payload, token=token)
    print("CREATE_LOGBOOK", code, body)
    if code != 200:
        return 1

    code, body = call("GET", f"{args.base_url}/api/logbook/entries", token=token)
    if code != 200:
        print("LIST_LOGBOOK", code, body)
        return 1
    entries = json.loads(body)
    entry_id = next((item["id"] for item in entries if smoke_marker in (item.get("title") or "")), "")
    if not entry_id:
        print("FAIL missing logbook entry in list")
        return 1

    # Promote to knowledge
    code, body = call("POST", f"{args.base_url}/api/logbook/entries/{entry_id}/promote-to-knowledge", {}, token=token)
    print("PROMOTE", code, body)
    if code != 200:
        return 1
    knowledge_entry_id = json.loads(body).get("knowledge_entry_id", "")
    if not knowledge_entry_id:
        print("FAIL missing knowledge_entry_id")
        return 1

    # Run AutoTest (expects AUTOTEST_MODE=simulated in delivery/CI)
    zip_bytes = build_autotest_zip_bytes()
    code, body = call_multipart(
        url=f"{args.base_url}/api/autotest/run",
        fields={},
        file_field="file",
        filename=f"smoke_{smoke_id}.zip",
        file_bytes=zip_bytes,
        content_type="application/zip",
        token=token,
    )
    print("AUTOTEST", code, body[:4000])
    if code != 200:
        return 1
    run = json.loads(body)
    if not run.get("execution_mode") or not run.get("project_type_detected") or run.get("working_directory") is None:
        print("FAIL autotest response missing execution fields")
        return 1

    # QA should find the promoted knowledge via its unique marker
    time.sleep(0.4)
    code, body = call("POST", f"{args.base_url}/api/qa", {"question": smoke_marker}, token=token)
    print("QA", code, body[:2000])
    if code != 200:
        return 1
    qa = json.loads(body)
    sources = qa.get("sources") or []
    if not any(smoke_marker in (src.get("title", "") or "") for src in sources):
        print("FAIL QA did not return promoted knowledge as a source")
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
