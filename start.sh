#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
for command in node npm ffmpeg ffprobe; do
  command -v "$command" >/dev/null || { echo "Missing $command. Install Node 20+ and FFmpeg (macOS: brew install node ffmpeg)."; exit 1; }
done
node -e 'if (Number(process.versions.node.split(".")[0]) < 20) process.exit(1)' || { echo 'Node 20+ required'; exit 1; }
if [[ ! -x .venv/bin/python ]]; then
  python_bin="${CCTV_PYTHON:-}"
  if [[ -z "$python_bin" ]]; then
    for candidate in python3.11 python3.12 python3.13 python3; do
      if command -v "$candidate" >/dev/null; then python_bin="$candidate"; break; fi
    done
  fi
  [[ -n "$python_bin" ]] || { echo 'Install Python 3.11+ first.'; exit 1; }
  "$python_bin" -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11+ required"'
  "$python_bin" -m venv .venv
fi
source .venv/bin/activate
mkdir -p logs data/models
if [[ ! -f .venv/requirements.sha256 ]] || ! shasum -a 256 -c .venv/requirements.sha256 >/dev/null 2>&1; then
  python -m pip install -r requirements.txt
  shasum -a 256 requirements.txt > .venv/requirements.sha256
fi
python -m pip check
if [[ ! -d frontend/node_modules ]] || [[ ! -f frontend/node_modules/.cctv-lock ]] || ! cmp -s frontend/package-lock.json frontend/node_modules/.cctv-lock; then
  npm ci --prefix frontend
  cp frontend/package-lock.json frontend/node_modules/.cctv-lock
fi
python - <<'PY'
import socket
for port in (8000,5173):
 with socket.socket() as s:
  s.settimeout(0.5)
  if s.connect_ex(('127.0.0.1',port)) == 0:
   raise SystemExit(f'Port {port} is in use. Stop the existing server before starting another instance.')
PY
backend_pid=''
frontend_pid=''
cleanup() {
  trap - INT TERM EXIT
  [[ -z "$frontend_pid" ]] || kill -TERM "$frontend_pid" 2>/dev/null || true
  [[ -z "$backend_pid" ]] || kill -TERM "$backend_pid" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 >logs/backend.log 2>&1 & backend_pid=$!
(cd frontend && exec node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort) >logs/frontend.log 2>&1 & frontend_pid=$!
echo 'Frontend: http://localhost:5173'
echo 'Backend:  http://localhost:8000'
echo 'Health:   http://localhost:8000/api/system/health'
echo 'Logs: logs/backend.log and logs/frontend.log. Ctrl+C stops both services.'
while kill -0 "$backend_pid" 2>/dev/null && kill -0 "$frontend_pid" 2>/dev/null; do sleep 2; done
echo 'A service stopped. Check logs for details.'
exit 1
