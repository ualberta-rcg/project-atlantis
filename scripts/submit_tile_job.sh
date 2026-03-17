#!/bin/bash
#SBATCH --job-name=atlantis
#SBATCH --account=main
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=04:00:00
#SBATCH --output=logs/atlantis_%A_%a.out
#SBATCH --error=logs/atlantis_%A_%a.err

# Archaeology radar pipeline — Slurm job wrapper.
#
# Two modes:
#   1. Single tile:  TILE_ID=tile_31.85_30.94 sbatch submit_tile_job.sh
#   2. Batch (auto):  sbatch --array=1-100 submit_tile_job.sh
#      Each array task picks unclaimed tiles from target_tiles.json.
#
# Required env: CDSE_CLIENT_ID, CDSE_CLIENT_SECRET, GIT_SSH_COMMAND
#
# Optional env:
#   TILE_ID       — process this specific tile (single mode)
#   BATCH_SIZE    — tiles per job in batch mode (default: 3)
#   PROJECT_ROOT  — path to repo (default: ~/project-atlantis)
#   VENV          — path to venv (default: ~/venv_cdse)

set -euo pipefail

TILE_ID="${TILE_ID:-${1:-}}"
BATCH_SIZE="${BATCH_SIZE:-3}"
PROJECT_ROOT="${PROJECT_ROOT:-${HOME}/project-atlantis}"
VENV="${VENV:-${HOME}/venv_cdse}"
JOB_ID="${SLURM_ARRAY_JOB_ID:-${SLURM_JOB_ID:-$$}}_${SLURM_ARRAY_TASK_ID:-0}"
WORKDIR="/tmp/atlantis_${JOB_ID}"

# Stagger array task starts to avoid coordination races (0-60s based on task ID)
if [[ -n "${SLURM_ARRAY_TASK_ID:-}" ]]; then
    JITTER=$(( (SLURM_ARRAY_TASK_ID * 17) % 60 ))
    sleep "$JITTER"
fi

echo "=============================================="
echo "Atlantis pipeline — $(date)"
echo "  Tile:     ${TILE_ID:-AUTO (batch mode)}"
echo "  Job ID:   ${JOB_ID}"
echo "  Node:     $(hostname)"
echo "  Project:  $PROJECT_ROOT"
echo "  Workdir:  $WORKDIR"
echo "  Batch sz: $BATCH_SIZE"
echo "=============================================="

# Source env vars (separate from .bashrc which skips non-interactive shells)
if [[ -f "${HOME}/.atlantis_env" ]]; then
    source "${HOME}/.atlantis_env"
elif [[ -f "${HOME}/.bashrc" ]]; then
    # Fallback: try bashrc (may fail in non-interactive shells)
    bash -c "source ${HOME}/.bashrc 2>/dev/null; env" | grep -E '^(CDSE_|GIT_SSH|REPO_URL)' > /tmp/.atlantis_env_$$ 2>/dev/null
    source /tmp/.atlantis_env_$$ 2>/dev/null || true
    rm -f /tmp/.atlantis_env_$$
fi

# Activate venv
if [[ -d "$VENV" ]]; then
    source "${VENV}/bin/activate"
    echo "Activated venv: $(which python)"
fi

# Ensure env vars
for v in CDSE_CLIENT_ID CDSE_CLIENT_SECRET GIT_SSH_COMMAND; do
    if [[ -z "${!v:-}" ]]; then
        echo "ERROR: $v not set" >&2
        exit 1
    fi
done
export CDSE_CLIENT_ID CDSE_CLIENT_SECRET GIT_SSH_COMMAND

# Compute nodes may have broken proxy settings
unset http_proxy https_proxy no_proxy HTTP_PROXY HTTPS_PROXY

cd "$PROJECT_ROOT"
mkdir -p logs
git pull --rebase 2>/dev/null || true

mkdir -p "$WORKDIR"

if [[ -n "$TILE_ID" ]]; then
    # Single-tile mode
    python "${PROJECT_ROOT}/scripts/run_pipeline.py" \
        "$TILE_ID" \
        --workdir "$WORKDIR"
else
    # Batch mode: auto-pick unclaimed tiles
    python "${PROJECT_ROOT}/scripts/run_pipeline.py" \
        --batch-size "$BATCH_SIZE" \
        --workdir "$WORKDIR"
fi

rm -rf "$WORKDIR"

echo ""
echo "Job finished at $(date)"
