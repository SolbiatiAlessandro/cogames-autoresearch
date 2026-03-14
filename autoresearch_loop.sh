#!/usr/bin/env bash
# =============================================================================
# CoGames Autoresearch - Main Experiment Loop (v2)
#
# Fixes from mar7 session:
# - Aggressive process cleanup between runs (OOM fix)
# - Checkpoint archiving per commit hash
# - Updated best score reference
# =============================================================================

REPO="/workspace/cogames-autoresearch"
LOG="$REPO/autoresearch_loop.log"
PID_FILE="$REPO/autoresearch_loop.pid"
OPENCLAW_BIN="$(which openclaw 2>/dev/null || echo /usr/local/bin/openclaw)"
CLAUDE_BIN="$(which claude 2>/dev/null || echo /usr/bin/claude)"
WHATSAPP_NUMBER="+12065321138"
CHECKPOINT_DIR="$REPO/checkpoints"

AGENT_TIMEOUT=2400

# Ensure uv and other local bins are on PATH (needed on RunPod)
export PATH="$HOME/.local/bin:$PATH"
export UV_LINK_MODE=copy
export GH_TOKEN="${GH_TOKEN:-}"

cd "$REPO"
mkdir -p "$CHECKPOINT_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

send_whatsapp() {
    local msg="$1"
    log "WhatsApp: $msg"
    "$OPENCLAW_BIN" message send --channel whatsapp --target "$WHATSAPP_NUMBER" --message "$msg" >> "$LOG" 2>&1 || true
}

cleanup_processes() {
    log "Cleaning up stray processes..."
    pkill -f "multiprocessing.spawn" 2>/dev/null || true
    pkill -f "multiprocessing.resource_tracker" 2>/dev/null || true
    pkill -f "train\.py" 2>/dev/null || true
    pkill -f "pufferlib" 2>/dev/null || true
    sleep 5
    # Clear any leaked GPU memory
    python3 -c "import torch; torch.cuda.empty_cache()" 2>/dev/null || true
    log "Process cleanup done."
}

check_memory() {
    local FREE_GB
    if [[ -f /proc/meminfo ]]; then
        # Linux (pod)
        FREE_GB=$(awk '/MemAvailable/ {printf "%.1f", $2/1024/1024}' /proc/meminfo)
    else
        # macOS fallback
        FREE_GB=$(python3 -c "
import subprocess
out = subprocess.check_output(['vm_stat']).decode()
st = {}
for l in out.split('\n'):
    if ':' in l and 'page size' not in l:
        k,v = l.split(':',1)
        try: st[k.strip()] = int(v.strip().rstrip('.'))
        except: pass
print((st.get('Pages free',0) + st.get('Pages inactive',0)) * 16384 / 1e9)
" 2>/dev/null || echo "8")
    fi
    log "Memory: ~${FREE_GB}GB available"
    if python3 -c "import sys; sys.exit(0 if float('${FREE_GB}') >= 8.0 else 1)" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

archive_checkpoint() {
    local commit_hash="$1"
    local best_ckpt
    best_ckpt=$(ls -t "$REPO"/train_dir/*/model_*.pt 2>/dev/null | head -1)
    if [[ -n "$best_ckpt" && -n "$commit_hash" ]]; then
        local dest="$CHECKPOINT_DIR/$commit_hash"
        mkdir -p "$dest"
        cp "$best_ckpt" "$dest/model_final.pt"
        log "Archived checkpoint: $dest/model_final.pt"
    else
        log "No checkpoint found to archive."
    fi
}

get_best_score() {
    tail -n+2 "$REPO/results.tsv" 2>/dev/null | \
      sort -t$'\t' -k2 -rn | head -1 | cut -f2
}

log "=========================================="
log "CoGames Autoresearch Loop v2 STARTING"
log "PID: $$"
log "Repo: $REPO"
log "Branch: $(git branch --show-current 2>/dev/null || echo unknown)"
log "=========================================="

consecutive_crashes=0
experiment_count=0

while true; do
    experiment_count=$((experiment_count + 1))

    # === CLEANUP before each run ===
    cleanup_processes

    # === MEMORY CHECK ===
    if ! check_memory; then
        log "LOW MEMORY — running aggressive cleanup..."
        cleanup_processes
        sleep 30
        if ! check_memory; then
            log "Still low memory after cleanup. Waiting 2 min..."
            sleep 120
            if ! check_memory; then
                send_whatsapp "🚨 CoGames autoresearch: persistent low memory. Pausing loop."
                log "Persistent low memory. Exiting."
                exit 1
            fi
        fi
    fi

    # === Clean train_dir (keep disk tidy, saves nothing useful without archiving) ===
    rm -rf "$REPO/train_dir"
    mkdir -p "$REPO/train_dir"

    log ""
    log "--- Experiment iteration #$experiment_count ($(date)) ---"
    log "Git log:"
    git log --oneline -5 2>&1 >> "$LOG"

    BEST_SCORE=$(get_best_score)
    log "Current best score: $BEST_SCORE"

    PROMPT="You are an autonomous RL researcher running ONE experiment iteration on the CoGames autoresearch project.

Working directory: $REPO (you are already here)

=== RESEARCH BRIEF (from Alessandro) ===
Continue the research direction from yesterday's 12-march-night session.
The breakthrough config was: milestones_2:25 + role_conditional + penalize_vibe_change, ent_coef=0.10
It achieved hearts (1.8) and aligned junctions (0.1) for the first time.
Build incrementally on what's working. Try small variations and tweaks.
Do NOT make radical changes — iterate on the winning formula.

=== MEMORY SAFETY (CRITICAL) ===
This is a RunPod pod. Last session OOMed and killed the pod.
- Use VECTOR_NUM_ENVS=64, VECTOR_NUM_WORKERS=8 (DO NOT increase these)
- Before running train.py, check memory: awk '/MemAvailable/ {printf \"%.1fGB\", \$2/1024/1024}' /proc/meminfo
- If available memory < 30GB, report CRITICALLY_BLOCKED: low memory
- After training, check memory again. If it dropped below 20GB, report it.
- NEVER increase batch sizes or env counts beyond what's already in train.py.

=== CURRENT STATE ===
$(git log --oneline -8 2>/dev/null)

=== RESULTS SO FAR ===
$(cat results.tsv 2>/dev/null || echo 'no results yet')

=== CURRENT BEST SCORE: ${BEST_SCORE} ===

=== YOUR TASK: Run ONE complete experiment iteration ===

Follow program.md exactly. Summary of the loop:
1. Read program.md, knowledge/reward_variants.md, knowledge/training_tips.md
2. Look at results above — pick ONE new experiment idea NOT already tried
3. Build on the breakthrough: milestones_2:25 + role_conditional + penalize_vibe_change, ent_coef=0.10
4. Small incremental changes only. Tweak one thing at a time.
5. TIME BUDGET: default 600s. You may use 600 or 1200 max.
   If you increase TIME_BUDGET, also adjust the LR schedule.
6. Modify train.py (ONLY this file)
7. git add train.py results.tsv && git commit -m 'experiment: <description>'
8. Run: uv run train.py > run.log 2>&1 (WAIT for completion)
9. Check results: grep '^composite_score:\|^mean_reward:' run.log
10. If crash: tail -50 run.log, fix train.py, retry up to 2 times
11. Log to results.tsv
12. git add train.py results.tsv && git commit with status=keep or status=discard
    Do NOT use git reset --hard. Always commit with the result for history.
13. git push
14. End your response with exactly one of:
    EXPERIMENT_DONE: score=<score> status=keep|discard|crash description=<what you tried>
    CRITICALLY_BLOCKED: <reason>

DO NOT stop, DO NOT ask questions. Run the full experiment end-to-end."

    log "Spawning Claude Code for experiment #$experiment_count (timeout: ${AGENT_TIMEOUT}s)..."

    AGENT_OUTPUT=$(cd "$REPO" && perl -e "alarm($AGENT_TIMEOUT); exec @ARGV" -- "$CLAUDE_BIN" \
        --dangerously-skip-permissions \
        --print \
        "$PROMPT" \
        2>&1) || AGENT_EXIT=$?

    log "--- Agent output (last 50 lines) ---"
    echo "$AGENT_OUTPUT" | tail -50 >> "$LOG"
    log "--- End agent output ---"

    # === ARCHIVE CHECKPOINT (before any git reset) ===
    CURRENT_COMMIT=$(git rev-parse --short=7 HEAD 2>/dev/null)
    archive_checkpoint "$CURRENT_COMMIT"

    # === POST-RUN CLEANUP ===
    cleanup_processes

    # Check for critical block
    if echo "$AGENT_OUTPUT" | grep -q "CRITICALLY_BLOCKED"; then
        REASON=$(echo "$AGENT_OUTPUT" | grep "CRITICALLY_BLOCKED" | head -1)
        log "CRITICAL BLOCK DETECTED: $REASON"
        consecutive_crashes=$((consecutive_crashes + 1))
        send_whatsapp "🚨 CoGames autoresearch CRITICALLY BLOCKED (experiment #$experiment_count). $REASON"
        if [[ $consecutive_crashes -ge 3 ]]; then
            send_whatsapp "🛑 CoGames autoresearch stopped after 3 critical blocks in a row. Manual intervention needed."
            log "Too many consecutive critical blocks. Exiting."
            exit 1
        fi
        log "Sleeping 5 minutes before retrying..."
        sleep 300
    else
        consecutive_crashes=0
        DONE_LINE=$(echo "$AGENT_OUTPUT" | grep "EXPERIMENT_DONE" | head -1 || echo "")
        log "Experiment #$experiment_count complete. $DONE_LINE"

        # Push results to GitHub
        cd "$REPO" && git push >> "$LOG" 2>&1 || true

        log "Sleeping 10 seconds before next experiment..."
        sleep 10
    fi
done
