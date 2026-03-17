#!/bin/bash
# setup.sh — Bootstrap a new cluster for the Atlantis pipeline.
#
# Run this ONCE on each new cluster. It:
#   1. Creates a Python venv with required packages
#   2. Sets up SSH deploy key for Git push access
#   3. Adds env vars to .bashrc
#   4. Clones the repo (if not already cloned)
#   5. Installs Git LFS
#
# Prerequisites:
#   - Python 3.8+
#   - Git
#   - Slurm (srun/sbatch)
#   - Internet access from login node
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/ualberta-rcg/project-atlantis/main/scripts/setup.sh | bash
#   # OR
#   git clone git@github.com:ualberta-rcg/project-atlantis.git && cd project-atlantis && bash scripts/setup.sh
#
# After setup, configure your CDSE API credentials:
#   1. Go to https://dataspace.copernicus.eu → Dashboard → OAuth clients
#   2. Edit ~/.bashrc and fill in CDSE_CLIENT_ID and CDSE_CLIENT_SECRET

set -euo pipefail

REPO_URL="git@github.com:ualberta-rcg/project-atlantis.git"
VENV_DIR="${HOME}/venv_cdse"
PROJECT_DIR="${HOME}/project-atlantis"
KEY_PATH="${HOME}/.ssh/archaeology-deploy-key"

echo "=============================================="
echo "Atlantis Pipeline — Cluster Setup"
echo "  Host:    $(hostname)"
echo "  User:    $(whoami)"
echo "  Date:    $(date)"
echo "=============================================="

# ---- 1. Python venv ----
echo ""
echo "[1/5] Setting up Python venv at ${VENV_DIR}..."
if [[ -d "$VENV_DIR" ]]; then
    echo "  Venv exists, updating packages..."
    source "${VENV_DIR}/bin/activate"
else
    python3 -m venv "$VENV_DIR"
    source "${VENV_DIR}/bin/activate"
    echo "  Created venv."
fi

pip install --upgrade pip -q
pip install requests numpy rasterio Pillow scipy scikit-learn -q
echo "  Packages installed: $(python -c 'import requests, numpy, rasterio, PIL, scipy, sklearn; print("OK")')"

# ---- 2. SSH deploy key ----
echo ""
echo "[2/5] SSH deploy key..."
mkdir -p ~/.ssh
chmod 700 ~/.ssh

if [[ -f "$KEY_PATH" ]]; then
    echo "  Key exists at $KEY_PATH"
else
    ssh-keygen -t ed25519 -C "atlantis-$(hostname)" -f "$KEY_PATH" -N ""
    chmod 600 "$KEY_PATH"
    echo ""
    echo "  *** ACTION REQUIRED ***"
    echo "  Add this deploy key to GitHub (Settings → Deploy keys → Add, enable Write):"
    echo ""
    cat "${KEY_PATH}.pub"
    echo ""
    echo "  Then re-run this script, or run: git clone ${REPO_URL}"
    echo "  Press Enter when done..."
    read -r
fi

# ---- 3. Env vars ----
echo ""
echo "[3/5] Environment variables..."
ENV_FILE="${HOME}/.atlantis_env"
if [[ -f "$ENV_FILE" ]]; then
    echo "  ${ENV_FILE} exists"
else
    cat > "$ENV_FILE" << ENVEOF
# Atlantis pipeline environment — sourced by jobs and .bashrc
export REPO_URL="git@github.com:ualberta-rcg/project-atlantis.git"
export GIT_SSH_COMMAND="ssh -i \$HOME/.ssh/archaeology-deploy-key -o StrictHostKeyChecking=accept-new"
# CDSE API credentials — get from https://dataspace.copernicus.eu (Dashboard → OAuth clients)
export CDSE_CLIENT_ID=""
export CDSE_CLIENT_SECRET=""
ENVEOF
    chmod 600 "$ENV_FILE"
    echo "  Created ${ENV_FILE}"
    echo "  *** Edit ${ENV_FILE} to fill in CDSE_CLIENT_ID and CDSE_CLIENT_SECRET ***"
fi

# Also source from .bashrc for interactive use
MARKER="# Source Atlantis env"
if ! grep -q "$MARKER" ~/.bashrc 2>/dev/null; then
    echo "" >> ~/.bashrc
    echo "$MARKER" >> ~/.bashrc
    echo "[[ -f \"\${HOME}/.atlantis_env\" ]] && source \"\${HOME}/.atlantis_env\"" >> ~/.bashrc
    echo "  Added source line to .bashrc"
fi
source "$ENV_FILE" 2>/dev/null || true

# ---- 4. Clone repo ----
echo ""
echo "[4/5] Repository..."
if [[ -d "$PROJECT_DIR/.git" ]]; then
    echo "  Already cloned at $PROJECT_DIR"
    cd "$PROJECT_DIR"
    git pull --rebase 2>/dev/null || true
else
    echo "  Cloning ${REPO_URL}..."
    git clone "$REPO_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

# Set git identity for this repo
git config user.email "rcg@ualberta.ca"
git config user.name "UAlberta RCG"

# ---- 5. Git LFS ----
echo ""
echo "[5/5] Git LFS..."
if command -v git-lfs &>/dev/null; then
    git lfs install --local
    echo "  Git LFS configured."
else
    echo "  WARNING: git-lfs not found. Large .tif files won't download properly."
    echo "  Install with: sudo apt install git-lfs  (or module load git-lfs)"
fi

echo ""
echo "=============================================="
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit ~/.bashrc → fill in CDSE_CLIENT_ID and CDSE_CLIENT_SECRET"
echo "  2. source ~/.bashrc"
echo "  3. cd ${PROJECT_DIR}"
echo "  4. ./scripts/launch_scan.sh --jobs 100"
echo ""
echo "Or start a quick test:"
echo "  cd ${PROJECT_DIR}"
echo "  sbatch --export=ALL,TILE_ID=tile_31.8500_30.9550 scripts/submit_tile_job.sh"
echo "=============================================="
