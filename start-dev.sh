#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PATH="$ROOT_DIR/.tools/node/bin:$PATH"

if [[ ! -x "$ROOT_DIR/.venv/bin/uvicorn" ]]; then
  echo "Не найдены зависимости backend. Выполните: $ROOT_DIR/.venv/bin/pip install -r backend/requirements.txt"
  exit 1
fi

if [[ ! -d "$ROOT_DIR/frontend/node_modules" ]]; then
  echo "Не найдены зависимости frontend. Выполните: cd frontend && npm install"
  exit 1
fi

"$ROOT_DIR/.venv/bin/uvicorn" app.main:app --app-dir "$ROOT_DIR/backend" --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

cleanup() {
  kill "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

cd "$ROOT_DIR/frontend"
npm run dev -- --host 127.0.0.1
