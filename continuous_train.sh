#!/bin/bash
# Continuous training script for march-17-best-MAPPO-baseline
# Runs the best config indefinitely with regular checkpointing and metric reporting

set -e

REPO="/workspace/repos/cogames-autoresearch"
BRANCH="march-17-best-MAPPO-baseline"
LOG_DIR="$REPO/continuous_logs"
CHECKPOINT_INTERVAL=600  # Save checkpoint every 10 minutes

cd "$REPO"
git checkout "$BRANCH" 2>/dev/null || true

# Create log directory
mkdir -p "$LOG_DIR"

# Set up Python environment
# Note: Set ANTHROPIC_API_KEY in your environment before running this script
export UV_LINK_MODE=copy
export PATH="$HOME/.local/bin:$PATH"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting continuous training on branch: $BRANCH"
echo "Config: milestones_2:25 + role_cond + penalize_vibe, ent=0.15, gamma=0.999, gae=0.95"
echo "Best score so far: 73.2 (beat previous 69.7!)"
echo "Logs: $LOG_DIR"
echo "Mode: CONTINUOUS (will loop indefinitely, 10min runs)"
echo ""

RUN_COUNT=0

while true; do
    RUN_COUNT=$((RUN_COUNT + 1))
    RUN_ID="$(date +%s)_run${RUN_COUNT}"
    RUN_LOG="$LOG_DIR/run_${RUN_ID}.log"
    
    echo ""
    echo "========================================"
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] STARTING RUN #$RUN_COUNT"
    echo "========================================"
    echo "Run ID: $RUN_ID"
    echo "Log: $RUN_LOG"
    echo ""
    
    # Run training
    uv run train.py 2>&1 | tee "$RUN_LOG"
    EXIT_CODE=$?
    
    echo ""
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Run #$RUN_COUNT completed with exit code: $EXIT_CODE"
    
    # Extract final metrics
    if [ -f "$RUN_LOG" ]; then
        echo "=== FINAL METRICS ==="
        tail -50 "$RUN_LOG" | grep -E "composite_score|cogs_junctions_held|heart_amount" | head -5
    fi
    
    # Check if we should continue
    if [ $EXIT_CODE -ne 0 ]; then
        echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ⚠️  Training failed, waiting 30s before retry..."
        sleep 30
    else
        echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ✅ Training completed successfully, starting next run..."
        sleep 5
    fi
done
