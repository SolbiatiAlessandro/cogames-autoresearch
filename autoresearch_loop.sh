#!/usr/bin/env bash
# =============================================================================
# CoGames Autoresearch - Main Experiment Loop (v2)
#
# Fixes from mar7 session:
# - Aggressive process cleanup between runs (OOM fix)
# - Checkpoint archiving per commit hash
# - Updated best score reference
# =============================================================================

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

=== CURRENT STATE ===
$(git log --oneline -8 2>/dev/null)

=== RESULTS SO FAR ===
$(cat results.tsv 2>/dev/null || echo 'no results yet')

=== CURRENT BEST SCORE: ${BEST_SCORE} ===

=== ⚠️ REWARD HACKING WARNING ===
composite_score is the sum of ALL shaped rewards — it does NOT mean agents are winning.
The current best (234) has ZERO junctions held. Agents are just farming easy rewards.

results.tsv now tracks 20 game metrics alongside composite_score. Key ones:

OBJECTIVE (the actual game — are we winning?):
  - cogs_junctions_held: junctions held by our team (THE objective, currently 0!)
  - cogs_junctions_aligned: junctions we captured
  - clips_junctions_held: junctions held by enemy (currently ~1.2M — they own everything)

AGENT BEHAVIOR (are agents doing anything useful?):
  - aligned_by_agent / scrambled_by_agent: territory actions (currently 0!)
  - cells_visited, deaths, move_success/failed, vibe_changes

ECONOMY (resource flow):
  - carbon/oxygen/silicon/germanium_amount, carbon_deposited, heart_amount

GEAR (is specialization happening?):
  - miner/aligner/scrambler/scout_gained

After each run, grep the game metrics from run.log. Look at the full picture.
Pick the metric that looks most promising to improve — maybe it's getting agents
to actually align junctions, or pick up gear, or deposit resources.
Prioritize experiments that move the GAME metrics, not just composite_score.

=== YOUR TASK: Run ONE complete experiment iteration ===

Follow program.md exactly. Summary of the loop:
1. Read program.md and ALL files in knowledge/ (especially knowledge/findings.md — critical lessons from previous sessions)
2. Look at results above — pick ONE new experiment idea NOT already tried
3. The best combo so far: milestones + role_conditional + penalize_vibe_change + credit + scout (score 234.0)
4. Be creative — explore new hyperparams, architecture, variant combos, or revisit promising ideas with tweaks.
5. TIME BUDGET: You may change TIME_BUDGET in train.py by monkey-patching:
   Add near top of main(): import prepare; prepare.TIME_BUDGET = <seconds>
   Default is 600s. You may use 600, 1200, or 1800.
   IMPORTANT: If you increase TIME_BUDGET, also adjust the LR schedule —
   the default schedule decays LR to near-zero at 600s. For longer runs,
   you may need to increase the learning rate or use a different schedule.
6. Modify train.py (ONLY this file)
7. git add train.py && git commit -m 'experiment: <description>'
8. Run: uv run train.py > run.log 2>&1 (WAIT for completion)
9. Check results: grep '^composite_score:\|^mean_reward:' run.log
10. If crash: tail -50 run.log, fix train.py, retry up to 2 times
11. Log to results.tsv
12. If score > ${BEST_SCORE}: KEEP commit. Otherwise: git reset --hard HEAD~1
13. End your response with exactly one of:
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

        # Sync to Notion
        bash "$REPO/sync_notion.sh" >> "$LOG" 2>&1 &

        # Push results to GitHub
        cd "$REPO" && git push >> "$LOG" 2>&1 || true

        log "Sleeping 10 seconds before next experiment..."
        sleep 10
    fi
done
