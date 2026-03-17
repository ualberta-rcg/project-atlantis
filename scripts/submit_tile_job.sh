#!/bin/bash
#SBATCH --job-name=atlantis
#SBATCH --account=main
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=logs/atlantis_%j.out
#SBATCH --error=logs/atlantis_%j.err

# Archaeology radar pipeline — Slurm job wrapper.
#
# Processes a single tile: fetch S1 imagery, build stack, run all scan types,
# generate PNGs, copy to repo, push.
#
# Required env: CDSE_CLIENT_ID, CDSE_CLIENT_SECRET, GIT_SSH_COMMAND
# Pass TILE_ID as env var or first argument.
#
# Usage:
#   TILE_ID=tile_31.8500_30.9400 sbatch scripts/submit_tile_job.sh
#   sbatch --export=ALL,TILE_ID=tile_31.8500_30.9400 scripts/submit_tile_job.sh

set -euo pipefail

TILE_ID="${TILE_ID:-${1:-}}"
if [[ -z "$TILE_ID" ]]; then
    echo "ERROR: TILE_ID not set. Pass as env var or argument." >&2
    exit 1
fi

PROJECT_ROOT="${PROJECT_ROOT:-${HOME}/project-atlantis}"
VENV="${VENV:-${HOME}/venv_cdse}"
WORKDIR="/tmp/atlantis_${SLURM_JOB_ID:-$$}"

echo "=============================================="
echo "Atlantis pipeline — $(date)"
echo "  Tile:     $TILE_ID"
echo "  Job ID:   ${SLURM_JOB_ID:-local}"
echo "  Node:     $(hostname)"
echo "  Project:  $PROJECT_ROOT"
echo "  Workdir:  $WORKDIR"
echo "=============================================="

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

# Pull latest repo state
cd "$PROJECT_ROOT"
git pull --rebase 2>/dev/null || true

# Create workdir
mkdir -p "$WORKDIR"

# Run pipeline with temp workdir
python "${PROJECT_ROOT}/scripts/run_pipeline.py" \
    "$TILE_ID" \
    --workdir "$WORKDIR"

# Cleanup
rm -rf "$WORKDIR"

echo ""
echo "Job finished at $(date)"
