#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$HOME/Projects/siyana-ai"
VENV_DIR="$PROJECT_DIR/.venv"
MODEL_PATH="$PROJECT_DIR/model/Qwen3-4B-Q4_K_M.gguf"
BACKEND_MODULE="prototype.backend.app.main:app"
HOST="127.0.0.1"
PORT="8000"

cd "$PROJECT_DIR"

echo
echo "============================================================"
echo "Starting Siyana AI"
echo "============================================================"
echo

if [ ! -d "$VENV_DIR" ]; then
    echo "ERROR: Python virtual environment was not found:"
    echo "$VENV_DIR"
    echo
    echo "Create it with:"
    echo "python3 -m venv .venv"
    exit 1
fi

if [ ! -f "$MODEL_PATH" ]; then
    echo "ERROR: The selected GGUF model was not found:"
    echo "$MODEL_PATH"
    echo
    echo "Run:"
    echo "bash download_model.sh"
    exit 1
fi

if [ ! -x "$VENV_DIR/bin/llama-server" ]; then
    echo "ERROR: llama-server was not found in the virtual environment:"
    echo "$VENV_DIR/bin/llama-server"
    echo
    echo "Expected a symbolic link or executable at this location."
    exit 1
fi

if [ ! -f "$PROJECT_DIR/config/system_prompt.txt" ]; then
    echo "ERROR: The Siyana AI system prompt was not found."
    exit 1
fi

if [ ! -f "$PROJECT_DIR/prototype/backend/app/main.py" ]; then
    echo "ERROR: The FastAPI backend was not found."
    exit 1
fi

if [ ! -f "$PROJECT_DIR/prototype/frontend/index.html" ]; then
    echo "ERROR: The frontend was not found."
    exit 1
fi

source "$VENV_DIR/bin/activate"

echo "Python:"
python --version

echo
echo "Model:"
ls -lh "$MODEL_PATH"

echo
echo "Stopping old Siyana AI processes, if any..."

pkill -f "uvicorn.*prototype.backend.app.main" 2>/dev/null || true
pkill -f llama-server 2>/dev/null || true

sleep 1

if ss -ltn 2>/dev/null | grep -q ":$PORT "; then
    echo "ERROR: Port $PORT is already in use."
    echo
    echo "Check the process with:"
    echo "ss -ltnp | grep ':$PORT'"
    exit 1
fi

echo
echo "Starting the local application..."
echo
echo "Open this address after startup:"
echo "http://$HOST:$PORT"
echo
echo "Press Ctrl+C to stop Siyana AI."
echo

exec python -m uvicorn \
    "$BACKEND_MODULE" \
    --host "$HOST" \
    --port "$PORT"
