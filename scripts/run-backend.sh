#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Starting FastAPI at http://127.0.0.1:8000"
exec uv run uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
