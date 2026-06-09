#!/bin/bash
set -euxo pipefail

ollama pull nomic-embed-text

# Smaller model for Codespaces
ollama pull phi3:mini

# Uncomment if you really need it
# ollama pull llama3    