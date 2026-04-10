from __future__ import annotations

import argparse
import json
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


def main() -> int:
    parser = argparse.ArgumentParser(description='Basic delivery smoke check for Enterprise AI Assistant')
    parser.add_argument('--base-url', default='http://localhost:8000')
    parser.add_argument('--user-id', default='admin')
    parser.add_argument('--password', required=True)
    args = parser.parse_args()

    status_code, body = call('POST', f"{args.base_url}/api/login", {'user_id': args.user_id, 'password': args.password})
    print('LOGIN', status_code, body)
    if status_code != 200:
        return 1

    token = json.loads(body)['access_token']
    for path in ['/api/me', '/api/docs']:
        code, response_body = call('GET', f'{args.base_url}{path}', token=token)
        print(path, code, response_body)
        if code != 200:
            return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
