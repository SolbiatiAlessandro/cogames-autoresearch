#!/bin/bash
# Continuous training script for march-17-best-MAPPO-baseline
# Runs the best config (96b72bf) indefinitely with regular checkpointing and metric reporting

set -e

REPO="/workspace/repos/cogames-autoresearch"
BRANCH="march-17-best-MAPPO-baseline"
LOG_DIR="$REPO/continuous_logs"
CHECKPOINT_INTERVAL=600  # Save checkpoint every 10 minutes

cd "$REPO"
git checkout "$BRANCH"

# Create log directory
mkdir -p "$LOG_DIR"

# Set up Python environment
# Note: Set ANTHROPIC_API_KEY in your environment before running this script
# export ANTHROPIC_API_KEY="your-key-here"
export UV_LINK_MODE=copy
export PATH="$HOME/.local/bin:$PATH"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting continuous training on branch: $BRANCH"
echo "Config: milestones_2:25 + role_cond + penalize_vibe, ent=0.15, gamma=0.999, gae=0.95"
echo "Best score so far: 69.7 | junctions: 1029.8"
echo "Logs: $LOG_DIR"
echo ""

RUN_ID=$(date +%s)
RUN_LOG="$LOG_DIR/run_${RUN_ID}.log"
METRICS_LOG="$LOG_DIR/metrics_${RUN_ID}.jsonl"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Run ID: $RUN_ID"
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Training log: $RUN_LOG"
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Metrics log: $METRICS_LOG"

# Run training with tee to both file and stdout
uv run train.py 2>&1 | tee "$RUN_LOG" &
TRAIN_PID=$!

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Training started (PID: $TRAIN_PID)"

# Monitor and report metrics
while kill -0 $TRAIN_PID 2>/dev/null; do
    sleep 60  # Check every minute
    
    # Extract latest metrics from log
    if [ -f "$RUN_LOG" ]; then
        LATEST=$(tail -100 "$RUN_LOG" | grep -E "global_step|composite_score|cogs_junctions_held" | tail -5)
        if [ ! -z "$LATEST" ]; then
            echo ""
            echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] === METRICS UPDATE ==="
            echo "$LATEST"
            echo ""
        fi
    fi
done

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Training process exited"
wait $TRAIN_PID
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Training completed successfully"
else
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Training failed with exit code: $EXIT_CODE"
fi

# Save final results
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Final metrics:"
tail -50 "$RUN_LOG" | grep -E "composite_score|cogs_junctions_held|mean_reward"

exit $EXIT_CODE
