from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_version_file() -> str:
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def read_frontend_version() -> str:
    package_json = ROOT / "frontend" / "package.json"
    data = json.loads(package_json.read_text(encoding="utf-8"))
    return str(data.get("version", "")).strip()


def main() -> int:
    version = read_version_file()
    frontend_version = read_frontend_version()
    errors: list[str] = []

    if not version:
        errors.append("VERSION is empty.")
    if frontend_version != version:
        errors.append(f"frontend/package.json version '{frontend_version}' != VERSION '{version}'")

    if errors:
        print("Version consistency check FAILED:")
        for err in errors:
            print(f"- {err}")
        return 1

    print(f"Version consistency check OK: {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

