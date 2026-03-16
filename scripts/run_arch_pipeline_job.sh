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
# Optional: request a GPU (e.g. for future ML step)
# #SBATCH --gres=gpu:1
# #SBATCH --constraint=volta  # or p100, 1080ti - adjust to your cluster

# Run archaeology pipeline for one site. Set SITE_ID and CDSE credentials.
# Optional: PATHWAY (default: first in config/pathways.json), CLUSTER_ID for process_record.
# Example: export SITE_ID=qubbet_el_hawa; export CDSE_CLIENT_ID=...; export CDSE_CLIENT_SECRET=...; sbatch run_arch_pipeline_job.sh

SITE_ID="${SITE_ID:-qubbet_el_hawa}"
PATHWAY="${PATHWAY:-}"
PROJECT_ROOT="${PROJECT_ROOT:-$SLURM_SUBMIT_DIR}"
VENV="${PROJECT_ROOT}/venv_cdse"

set -e
echo "=== Arch pipeline job started at $(date) ==="
echo "Site: $SITE_ID Pathway: ${PATHWAY:-<default>}"
echo "Project: $PROJECT_ROOT"

if [[ -z "$CDSE_CLIENT_ID" || -z "$CDSE_CLIENT_SECRET" ]]; then
  echo "Set CDSE_CLIENT_ID and CDSE_CLIENT_SECRET (e.g. in job script or export before sbatch)" >&2
  exit 1
fi

export CDSE_CLIENT_ID CDSE_CLIENT_SECRET
cd "$PROJECT_ROOT"
source "${VENV}/bin/activate" 2>/dev/null || true
if [[ -n "$PATHWAY" ]]; then
  python "${PROJECT_ROOT}/scripts/run_pipeline.py" "$SITE_ID" --pathway "$PATHWAY"
else
  python "${PROJECT_ROOT}/scripts/run_pipeline.py" "$SITE_ID"
fi

echo "=== Job finished at $(date) ==="
