#!/bin/bash
# launch_scan.sh — Generate tile grid and submit Slurm job array.
#
# This is the one command you run to start scanning. It:
#   1. Generates target_tiles.json from scan.json regions (or a custom bbox)
#   2. Commits and pushes so all clusters see the same tile list
#   3. Submits a Slurm array of N jobs, each picking unclaimed tiles
#
# Usage:
#   ./scripts/launch_scan.sh                        # all regions, 100 jobs
#   ./scripts/launch_scan.sh --jobs 1000            # all regions, 1000 jobs
#   ./scripts/launch_scan.sh --region western_desert_egypt --jobs 50
#   ./scripts/launch_scan.sh --bbox 25,22,30,27 --jobs 200
#   ./scripts/launch_scan.sh --jobs 500 --batch-size 5 --time 08:00:00
#
# On a new cluster, run setup.sh first (creates venv, sets env vars).

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# ---- Defaults ----
JOBS=100
BATCH_SIZE=3
REGION=""
BBOX=""
TIME="04:00:00"
PARTITION="compute"
ACCOUNT="main"
MEM="8G"
CPUS=2
DRY_RUN=false
SKIP_GENERATE=false

# ---- Parse args ----
while [[ $# -gt 0 ]]; do
    case "$1" in
        --jobs)       JOBS="$2"; shift 2;;
        --batch-size) BATCH_SIZE="$2"; shift 2;;
        --region)     REGION="$2"; shift 2;;
        --bbox)       BBOX="$2"; shift 2;;
        --time)       TIME="$2"; shift 2;;
        --partition)  PARTITION="$2"; shift 2;;
        --account)    ACCOUNT="$2"; shift 2;;
        --mem)        MEM="$2"; shift 2;;
        --cpus)       CPUS="$2"; shift 2;;
        --dry-run)    DRY_RUN=true; shift;;
        --skip-generate) SKIP_GENERATE=true; shift;;
        -h|--help)
            echo "Usage: $0 [--jobs N] [--batch-size N] [--region NAME] [--bbox min_lon,min_lat,max_lon,max_lat] [--time HH:MM:SS] [--dry-run]"
            exit 0;;
        *) echo "Unknown arg: $1" >&2; exit 1;;
    esac
done

echo "=============================================="
echo "Atlantis Scan Launcher"
echo "  Project:    $PROJECT_ROOT"
echo "  Jobs:       $JOBS"
echo "  Batch size: $BATCH_SIZE tiles/job"
echo "  Region:     ${REGION:-all from scan.json}"
echo "  Time/job:   $TIME"
echo "=============================================="

# ---- Step 1: Generate target tiles ----
if [[ "$SKIP_GENERATE" == "false" ]]; then
    echo ""
    echo "[1/3] Generating target tiles..."

    VENV="${VENV:-${HOME}/venv_cdse}"
    if [[ -d "$VENV" ]]; then
        source "${VENV}/bin/activate"
    fi

    if [[ -n "$BBOX" ]]; then
        IFS=',' read -r BLON1 BLAT1 BLON2 BLAT2 <<< "$BBOX"
        python scripts/generate_target_tiles.py \
            --min-lon "$BLON1" --min-lat "$BLAT1" \
            --max-lon "$BLON2" --max-lat "$BLAT2"
    elif [[ -n "$REGION" ]]; then
        python -c "
import json, sys
sys.path.insert(0, 'scripts')
from generate_target_tiles import generate_region

with open('config/scan.json') as f:
    sc = json.load(f)
defaults = sc.get('tile_defaults', {})
size_km = defaults.get('size_km', 5)
res_m = defaults.get('resolution_m', 10)

region = next((r for r in sc['scan_regions'] if r['name'] == '$REGION'), None)
if not region:
    names = [r['name'] for r in sc['scan_regions']]
    print(f'Region $REGION not found. Available: {names}', file=sys.stderr)
    sys.exit(1)

b = region['bounds']
tiles = generate_region(b['min_lon'], b['max_lon'], b['min_lat'], b['max_lat'], size_km, res_m)

# Merge with existing tiles (keep manually-added ones)
import os
existing_path = 'config/target_tiles.json'
existing = []
if os.path.isfile(existing_path):
    with open(existing_path) as f:
        existing = json.load(f)
existing_ids = {t['tile_id'] for t in existing}
new = [t for t in tiles if t['tile_id'] not in existing_ids]
merged = existing + new

with open(existing_path, 'w') as f:
    json.dump(merged, f, indent=2)
print(f'Added {len(new)} tiles for {region[\"name\"]} (total: {len(merged)})')
"
    else
        python scripts/generate_target_tiles.py --from-scan
    fi

    TILE_COUNT=$(python -c "import json; print(len(json.load(open('config/target_tiles.json'))))")
    echo "  Target tiles: $TILE_COUNT"

    # Check how many already done
    DONE_COUNT=0
    if [[ -f processed_tiles.jsonl ]]; then
        DONE_COUNT=$(wc -l < processed_tiles.jsonl)
    fi
    REMAINING=$((TILE_COUNT - DONE_COUNT))
    echo "  Already processed: $DONE_COUNT"
    echo "  Remaining: $REMAINING"

    if [[ "$REMAINING" -le 0 ]]; then
        echo "All tiles processed! Nothing to do."
        exit 0
    fi

    # Cap jobs at remaining tiles / batch_size
    MAX_USEFUL_JOBS=$(( (REMAINING + BATCH_SIZE - 1) / BATCH_SIZE ))
    if [[ "$JOBS" -gt "$MAX_USEFUL_JOBS" ]]; then
        echo "  Capping jobs from $JOBS to $MAX_USEFUL_JOBS (enough for remaining tiles)"
        JOBS=$MAX_USEFUL_JOBS
    fi
else
    echo "[1/3] Skipping tile generation (--skip-generate)"
fi

# ---- Step 2: Commit and push tile list ----
echo ""
echo "[2/3] Syncing tile list to repo..."
git add config/target_tiles.json
if git diff --cached --quiet; then
    echo "  No changes to tile list."
else
    git commit -m "Update target_tiles.json ($(python -c "import json; print(len(json.load(open('config/target_tiles.json'))))" ) tiles)"
    git push 2>&1 || { git pull --rebase && git push; }
    echo "  Pushed."
fi

# ---- Step 3: Submit Slurm array ----
echo ""
echo "[3/3] Submitting Slurm array: $JOBS jobs..."

mkdir -p logs

if [[ "$DRY_RUN" == "true" ]]; then
    echo "  DRY RUN — would submit:"
    echo "    sbatch --array=1-${JOBS}%20 \\"
    echo "      --export=ALL,BATCH_SIZE=${BATCH_SIZE} \\"
    echo "      --time=${TIME} --partition=${PARTITION} --account=${ACCOUNT} \\"
    echo "      --mem=${MEM} --cpus-per-task=${CPUS} \\"
    echo "      scripts/submit_tile_job.sh"
    echo ""
    echo "  Remove --dry-run to actually submit."
    exit 0
fi

# %20 = max 20 concurrent jobs (prevents API flooding)
# Use --export=NONE so env doesn't leak (job sources .bashrc itself)
JOBID=$(sbatch \
    --array=1-${JOBS}%20 \
    --export=NONE,BATCH_SIZE=${BATCH_SIZE} \
    --time="${TIME}" \
    --partition="${PARTITION}" \
    --account="${ACCOUNT}" \
    --mem="${MEM}" \
    --cpus-per-task="${CPUS}" \
    --parsable \
    scripts/submit_tile_job.sh)

echo "  Submitted array job: $JOBID"
echo "  Tasks: 1-${JOBS} (max 20 concurrent)"
echo "  Tiles/task: $BATCH_SIZE"
echo "  Time/task: $TIME"
echo ""
echo "Monitor with:"
echo "  squeue -u \$(whoami)"
echo "  tail -f logs/atlantis_${JOBID}_*.out"
echo "  wc -l processed_tiles.jsonl    # tiles completed"
echo ""
echo "Re-run this script to submit more jobs as needed."
echo "Jobs on other clusters will coordinate automatically via Git."
