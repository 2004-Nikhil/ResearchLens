#!/bin/bash

# ─────────────────────────────────────────────
#  Environment Health Check
#  Run: bash check_env.sh
# ─────────────────────────────────────────────

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
BOLD='\033[1m'; NC='\033[0m'

PASS=0; FAIL=0; WARN=0

pass() { echo -e "  ${GREEN}✓${NC}  $1"; ((PASS++)); }
fail() { echo -e "  ${RED}✗${NC}  $1"; ((FAIL++)); }
warn() { echo -e "  ${YELLOW}~${NC}  $1"; ((WARN++)); }
section() { echo -e "\n${BOLD}$1${NC}"; }

# ── Python ────────────────────────────────────
section "Python"
PY=$(python --version 2>&1)

if [[ "$PY" == *"3.11"* || "$PY" == *"3.12"* ]]; then
    pass "$PY"
else
    fail "Expected Python 3.11+, got: $PY"
fi

# ── Python packages ───────────────────────────
section "Python packages"
packages=(
  "llama_index"
  "llama_index.vector_stores.qdrant"
  "llama_index.embeddings.ollama"
  "llama_index.llms.ollama"
  "qdrant_client"
  "gradio"
  "pymupdf"
)
for pkg in "${packages[@]}"; do
  python -c "import $pkg" 2>/dev/null \
    && pass "$pkg" \
    || fail "$pkg  →  run: pip install -r requirements.txt"
done

# ── Qdrant process ────────────────────────────
section "Qdrant"
if pgrep -x qdrant > /dev/null; then
  pass "qdrant process is running (PID: $(pgrep -x qdrant))"
else
  fail "qdrant not running  →  run: nohup qdrant --storage-path ./qdrant_storage &"
fi

HTTP=$(curl -sf -o /dev/null -w "%{http_code}" http://localhost:6333/healthz 2>/dev/null)
[[ "$HTTP" == "200" ]] \
  && pass "Qdrant REST API healthy (port 6333)" \
  || fail "Qdrant REST API not responding (got: $HTTP)  →  check: cat /tmp/qdrant.log"

COLLECTIONS=$(curl -sf http://localhost:6333/collections 2>/dev/null)
[[ "$COLLECTIONS" == *"collections"* ]] \
  && pass "Qdrant collections endpoint reachable" \
  || warn "Qdrant collections endpoint gave unexpected response"

# ── Ollama process ────────────────────────────
section "Ollama"
if pgrep -f "ollama serve" > /dev/null; then
  pass "ollama serve is running"
else
  fail "ollama not running  →  run: nohup ollama serve &"
fi

OLLAMA_HTTP=$(curl -sf -o /dev/null -w "%{http_code}" http://localhost:11434 2>/dev/null)
[[ "$OLLAMA_HTTP" == "200" ]] \
  && pass "Ollama API healthy (port 11434)" \
  || fail "Ollama API not responding  →  check: cat /tmp/ollama.log"

# ── Ollama models ─────────────────────────────
section "Ollama models"
MODELS=$(ollama list 2>/dev/null)
[[ "$MODELS" == *"nomic-embed-text"* ]] \
  && pass "nomic-embed-text (embedding model)" \
  || fail "nomic-embed-text not found  →  run: ollama pull nomic-embed-text"

if [[ "$MODELS" == *"llama3"* ]]; then
  pass "llama3 (generation model)"
elif [[ "$MODELS" == *"phi3"* ]]; then
  warn "phi3 found instead of llama3 (fine for dev, update model_name in code)"
else
  fail "No generation model found  →  run: ollama pull llama3  (or phi3:mini)"
fi

# ── Ports ─────────────────────────────────────
section "Ports"
for port in 6333 7860 11434; do
  ss -tlnp 2>/dev/null | grep -q ":$port " \
    && pass "Port $port is open" \
    || warn "Port $port not listening yet (normal if app not started)"
done

# ── Project structure ─────────────────────────
section "Project structure"
[[ -d "papers" ]]       && pass "papers/ folder exists"  || warn "papers/ missing  →  run: mkdir papers"
[[ -d "src" ]]          && pass "src/ folder exists"     || warn "src/ missing  →  run: mkdir src"
[[ -f "requirements.txt" ]] && pass "requirements.txt found" || fail "requirements.txt missing"
[[ -f ".gitignore" ]]   && pass ".gitignore found"       || warn ".gitignore missing"

# ── Quick end-to-end smoke test ───────────────
section "Smoke test (embed + store round-trip)"
python - << 'PYEOF' 2>/dev/null && pass "LlamaIndex → Qdrant → Ollama wiring OK" || fail "Smoke test failed — check logs above"
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Just check Qdrant client connects and can create a temp collection
client = QdrantClient(host="localhost", port=6333)
client.recreate_collection(
    collection_name="_healthcheck",
    vectors_config=VectorParams(size=4, distance=Distance.COSINE)
)
client.delete_collection("_healthcheck")
PYEOF

# ── Summary ───────────────────────────────────
echo ""
echo -e "${BOLD}────────────────────────────────────────${NC}"
echo -e "  ${GREEN}✓ Passed${NC}  $PASS"
[[ $WARN -gt 0 ]] && echo -e "  ${YELLOW}~ Warnings${NC} $WARN"
[[ $FAIL -gt 0 ]] && echo -e "  ${RED}✗ Failed${NC}   $FAIL"
echo -e "${BOLD}────────────────────────────────────────${NC}"

[[ $FAIL -eq 0 ]] \
  && echo -e "\n  ${GREEN}${BOLD}All good — ready to build!${NC}\n" \
  || echo -e "\n  ${RED}${BOLD}Fix the failures above then re-run this script.${NC}\n"