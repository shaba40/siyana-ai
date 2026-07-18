#!/usr/bin/env bash

set -euo pipefail

echo "Stopping Siyana AI..."

pkill -f "uvicorn.*prototype.backend.app.main" 2>/dev/null || true
pkill -f llama-server 2>/dev/null || true

sleep 1

if pgrep -af "uvicorn.*prototype.backend.app.main|llama-server" \
    > /dev/null 2>&1; then
    echo "WARNING: One or more Siyana AI processes may still be running."
    pgrep -af "uvicorn.*prototype.backend.app.main|llama-server" || true
    exit 1
fi

echo "Siyana AI stopped."
