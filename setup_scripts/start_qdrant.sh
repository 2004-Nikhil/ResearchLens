#!/bin/bash
set -euxo pipefail

QDRANT_VERSION="v1.15.4"
INSTALL_DIR="$HOME/.local/bin"
QDRANT_CONFIG_DIR="$HOME/qdrant_config"
QDRANT_STORAGE_DIR="/workspaces/ResearchLens/qdrant_storage"

# Install directory
mkdir -p "$INSTALL_DIR"

# Install Qdrant if missing
if [ ! -f "$INSTALL_DIR/qdrant" ]; then
    echo "Installing Qdrant ${QDRANT_VERSION}..."

    curl -L \
      "https://github.com/qdrant/qdrant/releases/download/${QDRANT_VERSION}/qdrant-x86_64-unknown-linux-gnu.tar.gz" \
      -o /tmp/qdrant.tar.gz

    rm -rf /tmp/qdrant_extract
    mkdir -p /tmp/qdrant_extract

    tar -xzf /tmp/qdrant.tar.gz -C /tmp/qdrant_extract

    QDRANT_BIN=$(find /tmp/qdrant_extract -type f -name qdrant | head -n 1)

    if [ -z "$QDRANT_BIN" ]; then
        echo "ERROR: Could not find qdrant binary after extraction"
        exit 1
    fi

    cp "$QDRANT_BIN" "$INSTALL_DIR/qdrant"
    chmod +x "$INSTALL_DIR/qdrant"
fi

export PATH="$INSTALL_DIR:$PATH"

echo "Using:"
which qdrant

echo "Version:"
qdrant --version

# Create storage/config directories
mkdir -p "$QDRANT_STORAGE_DIR"
mkdir -p "$QDRANT_CONFIG_DIR"

# Create config
cat > "$QDRANT_CONFIG_DIR/config.yaml" << EOF
log_level: INFO

storage:
  storage_path: "$QDRANT_STORAGE_DIR"

service:
  host: 0.0.0.0
  http_port: 6333
  grpc_port: 6334
EOF

# Stop existing qdrant instance if running
if pgrep -x qdrant >/dev/null 2>&1; then
    echo "Stopping existing Qdrant..."
    pkill -x qdrant
    sleep 2
fi

echo "Starting Qdrant..."

nohup qdrant \
  --config-path "$QDRANT_CONFIG_DIR/config.yaml" \
  > /tmp/qdrant.log 2>&1 &

sleep 8

if curl -sf http://localhost:6333/healthz >/dev/null; then
    echo "✅ Qdrant started successfully"
    echo "Health endpoint: http://localhost:6333/healthz"
else
    echo "❌ Qdrant failed to start"
    echo ""
    echo "===== QDRANT LOG ====="
    cat /tmp/qdrant.log
    exit 1
fi