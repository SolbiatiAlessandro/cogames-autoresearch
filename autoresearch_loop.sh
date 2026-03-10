#!/usr/bin/env bash
# =============================================================================
# CoGames Autoresearch - Main Experiment Loop (v3)
#
# Changes from v2:
# - Creates a fresh autoresearch/<tag> branch per session (Karpathy pattern)
# - Fresh results.tsv per session (untracked by git)
# - Detects "Credit balance is too low" and exits instead of spinning
# - Better cost tracking
# =============================================================================

set -euo pipefail

REPO="$HOME/Projects/cogames-autoresearch"
LOG="$REPO/autoresearch_loop.log"
PID_FILE="$REPO/autoresearch_loop.pid"
OPENCLAW_BIN="/opt/homebrew/bin/openclaw"
CLAUDE_BIN="$HOME/.local/bin/claude"
WHATSAPP_NUMBER="+12065321138"
CHECKPOINT_DIR="$REPO/checkpoints"

AGENT_TIMEOUT=2400

cd "$REPO"
mkdir -p "$CHECKPOINT_DIR"

# =========================================================================
# Session setup: create a fresh branch (Karpathy pattern)
# =========================================================================

# Generate a run tag from today's date (mar9, mar9b, mar9c, ...)
BASE_TAG=$(date '+%b%-d' | tr '[:upper:]' '[:lower:]')
RUN_TAG="$BASE_TAG"
SUFFIX=""
while git rev-parse --verify "autoresearch/$RUN_TAG" >/dev/null 2>&1; do
    if [[ -z "$SUFFIX" ]]; then
        SUFFIX="b"
    else
        # increment: b->c, c->d, etc.
        SUFFIX=$(echo "$SUFFIX" | tr 'a-y' 'b-z')
    fi
    RUN_TAG="${BASE_TAG}${SUFFIX}"
done

BRANCH="autoresearch/$RUN_TAG"

# Make sure we're on main and up to date
git checkout main 2>/dev/null || true
git pull --rebase origin main 2>/dev/null || true

# Create the fresh session branch
git checkout -b "$BRANCH"

# Fresh results.tsv for this session (copy header + any historical context from main)
# Karpathy keeps results.tsv untracked; we start fresh but include the header
if [[ -f results.tsv ]]; then
    # Keep the existing file (has header + history from main)
    # The agent will append to it during this session
    :
else
    echo -e "commit\tcomposite_score\tmean_reward\tmemory_gb\tstatus\tdescription\te2e_seconds\tapi_cost_usd\tcogs_junctions_held\tcogs_junctions_aligned\tclips_junctions_held\taligned_by_agent\tscrambled_by_agent\tcells_visited\tdeaths\tmove_success\tmove_failed\tvibe_changes\tcarbon_deposited\tcarbon_amount\toxygen_amount\tsilicon_amount\tgermanium_amount\theart_amount\tminer_gained\taligner_gained\tscrambler_gained\tscout_gained" > results.tsv
fi

# =========================================================================
# Logging and helpers
# =========================================================================

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
    log "Process cleanup done."
}

check_memory() {
    local FREE_GB
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
    log "Memory: ~${FREE_GB}GB available"
    if python3 -c "import sys; sys.exit(0 if float('$FREE_GB') >= 3.0 else 1)" 2>/dev/null; then
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

# =========================================================================
# Save PID and announce
# =========================================================================

echo $$ > "$PID_FILE"

log "=========================================="
log "CoGames Autoresearch Loop v3 STARTING"
log "PID: $$"
log "Repo: $REPO"
log "Branch: $BRANCH (fresh session)"
log "=========================================="

send_whatsapp "🧪 CoGames autoresearch session started — branch $BRANCH"

consecutive_crashes=0
consecutive_credit_failures=0
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

    # === Clean train_dir (keep disk tidy) ===
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
Session branch: $BRANCH (experiment #$experiment_count)

=== CURRENT STATE ===
$(git log --oneline -8 2>/dev/null)

=== RESULTS SO FAR ===
$(cat results.tsv 2>/dev/null || echo 'no results yet')

=== CURRENT BEST SCORE: ${BEST_SCORE} ===

=== YOUR TASK: Run ONE complete experiment iteration ===

Follow program.md exactly — READ IT FIRST, especially the 'What Has Been Tried' and
'What Better Means' sections. Also read knowledge/findings.md for reward hacking analysis.

Summary of the loop:
1. Read program.md and ALL files in knowledge/ (especially findings.md)
2. Look at results above — pick ONE new experiment idea NOT already tried
3. Focus on GAME METRICS (cogs_junctions_held, aligned_by_agent), not just composite_score
4. Modify train.py (ONLY this file)
5. git add train.py && git commit -m 'experiment: <description> — <game metrics summary>'
6. Run: uv run train.py > run.log 2>&1 (WAIT for completion)
7. Check results: grep '^composite_score:\|^mean_reward:' run.log
8. Check game metrics: grep -A20 'Game Metrics' run.log
9. If crash: tail -50 run.log, fix train.py, retry up to 2 times
10. Log to results.tsv (train.py does this automatically)
11. If genuine game progress: KEEP commit. If reward hacking or worse: git reset --hard HEAD~1
12. End your response with exactly one of:
    EXPERIMENT_DONE: score=<score> status=keep|discard|crash description=<what you tried>
    CRITICALLY_BLOCKED: <reason>

DO NOT stop, DO NOT ask questions. Run the full experiment end-to-end."

    log "Spawning Claude Code for experiment #$experiment_count (timeout: ${AGENT_TIMEOUT}s)..."
    EXPERIMENT_START=$(date +%s)

    AGENT_OUTPUT=$(cd "$REPO" && perl -e "alarm($AGENT_TIMEOUT); exec @ARGV" -- "$CLAUDE_BIN" \
        --dangerously-skip-permissions \
        --print \
        "$PROMPT" \
        2>&1) || AGENT_EXIT=$?

    EXPERIMENT_END=$(date +%s)
    EXPERIMENT_ELAPSED=$(( EXPERIMENT_END - EXPERIMENT_START ))

    # ===================================================================
    # CHECK FOR CREDIT EXHAUSTION — exit instead of spinning
    # ===================================================================
    if echo "$AGENT_OUTPUT" | grep -qi "credit balance is too low\|insufficient credits\|billing\|rate limit.*exceeded\|quota exceeded"; then
        consecutive_credit_failures=$((consecutive_credit_failures + 1))
        log "⚠️ API CREDIT ISSUE detected (attempt $consecutive_credit_failures/3)"
        if [[ $consecutive_credit_failures -ge 3 ]]; then
            send_whatsapp "🛑 CoGames autoresearch: API credits exhausted after $experiment_count experiments on branch $BRANCH. Loop stopped."
            log "API credits exhausted after 3 consecutive failures. Exiting."
            exit 1
        fi
        log "Retrying in 60 seconds..."
        sleep 60
        continue
    fi
    consecutive_credit_failures=0

    # Estimate API cost from token counts in Claude output
    INPUT_KTOK=$(echo "$AGENT_OUTPUT" | grep -oE "[0-9]+(\.[0-9]+)?k in" | grep -oE "[0-9]+(\.[0-9]+)?" | tail -1 || echo "0")
    OUTPUT_KTOK=$(echo "$AGENT_OUTPUT" | grep -oE "[0-9]+(\.[0-9]+)?k out" | grep -oE "[0-9]+(\.[0-9]+)?" | tail -1 || echo "0")
    API_COST=$(python3 -c "
in_tok = float('${INPUT_KTOK}' or 0) * 1000
out_tok = float('${OUTPUT_KTOK}' or 0) * 1000
cost = (in_tok / 1_000_000 * 3.0) + (out_tok / 1_000_000 * 15.0)
print(f'{cost:.4f}')
" 2>/dev/null || echo "0.0000")
    echo "$API_COST" > "$REPO/.experiment_cost"
    log "Experiment #$experiment_count took ${EXPERIMENT_ELAPSED}s, estimated cost: \$${API_COST}"

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
        send_whatsapp "🚨 CoGames autoresearch CRITICALLY BLOCKED (experiment #$experiment_count on $BRANCH). $REASON"
        if [[ $consecutive_crashes -ge 3 ]]; then
            send_whatsapp "🛑 CoGames autoresearch stopped after 3 critical blocks on $BRANCH. Manual intervention needed."
            log "Too many consecutive critical blocks. Exiting."
            exit 1
        fi
        log "Sleeping 5 minutes before retrying..."
        sleep 300
    else
        consecutive_crashes=0
        DONE_LINE=$(echo "$AGENT_OUTPUT" | grep "EXPERIMENT_DONE" | head -1 || echo "")
        log "Experiment #$experiment_count complete. $DONE_LINE"

        # Sync to Notion
        bash "$REPO/sync_notion.sh" >> "$LOG" 2>&1 &

        # Push session branch to GitHub
        cd "$REPO" && git push -u origin "$BRANCH" >> "$LOG" 2>&1 || true

        log "Sleeping 10 seconds before next experiment..."
        sleep 10
    fi
done
