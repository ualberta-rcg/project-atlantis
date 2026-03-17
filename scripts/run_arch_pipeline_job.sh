#!/bin/bash
#SBATCH --job-name=arch_pipeline
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=arch_pipeline_%j.out
#SBATCH --error=arch_pipeline_%j.err

# v3: tile-based pipeline. Claims tiles from target_tiles.json, fetches once,
# runs all enabled scan types, pushes results.
#
# Required env vars: CDSE_CLIENT_ID, CDSE_CLIENT_SECRET, GIT_SSH_COMMAND
# Optional: TILE_ID (single tile test), BATCH_SIZE (default 5), REPO_URL
#
# Usage:
#   export CDSE_CLIENT_ID=... CDSE_CLIENT_SECRET=... GIT_SSH_COMMAND="ssh -i ~/.ssh/archaeology-deploy-key -o StrictHostKeyChecking=accept-new"
#   sbatch run_arch_pipeline_job.sh                          # claim-based batch
#   TILE_ID=tile_30.8740_29.2470 sbatch run_arch_pipeline_job.sh  # single tile

PROJECT_ROOT="${PROJECT_ROOT:-$SLURM_SUBMIT_DIR}"
VENV="${PROJECT_ROOT}/venv_cdse"
BATCH_SIZE="${BATCH_SIZE:-5}"

set -e
echo "=== Arch pipeline v3 started at $(date) ==="
echo "Project: $PROJECT_ROOT"

if [[ -z "$CDSE_CLIENT_ID" || -z "$CDSE_CLIENT_SECRET" ]]; then
  echo "Set CDSE_CLIENT_ID and CDSE_CLIENT_SECRET" >&2
  exit 1
fi

export CDSE_CLIENT_ID CDSE_CLIENT_SECRET
cd "$PROJECT_ROOT"
git pull --rebase || true
source "${VENV}/bin/activate" 2>/dev/null || true

if [[ -n "$TILE_ID" ]]; then
  python "${PROJECT_ROOT}/scripts/run_pipeline.py" "$TILE_ID"
else
  python "${PROJECT_ROOT}/scripts/run_pipeline.py" --batch-size "$BATCH_SIZE"
fi

echo "=== Job finished at $(date) ==="
