#!/bin/bash
set -euxo pipefail

echo "========================================="
echo "Setting up development environment"
echo "========================================="

# Upgrade pip
python -m pip install --upgrade pip

# Install requirements if present
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    echo "requirements.txt not found, skipping."
fi

# Create project structure
mkdir -p papers
mkdir -p src

touch src/__init__.py


sudo apt update
sudo apt install -y git-lfs
git lfs install

# Create .gitignore if absent
if [ ! -f .gitignore ]; then
cat > .gitignore << EOF
qdrant_storage/
papers/
__pycache__/
*.pyc
.env
EOF
fi

echo "========================================="
echo "Setup completed successfully"
echo "========================================="