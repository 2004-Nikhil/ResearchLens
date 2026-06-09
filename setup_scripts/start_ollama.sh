#!/bin/bash
set -euxo pipefail

sudo apt-get update
sudo apt-get install -y zstd

if ! command -v ollama >/dev/null 2>&1; then
    curl -fsSL https://ollama.com/install.sh | sh
fi

nohup ollama serve > /tmp/ollama.log 2>&1 &

sleep 5

ollama list || true

echo "Ollama started"