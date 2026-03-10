#!/usr/bin/env bash
# =============================================================================
# CoGames Autoresearch - Main Experiment Loop (v3)
#
# Each session:
# 1. Creates a fresh autoresearch/<tag> branch from main
# 2. Opens a GitHub Discussion as a session log
# 3. Saves results to results/results_<tag>.tsv
# 4. Updates the discussion after each experiment
# 5. Exits cleanly on credit exhaustion
# =============================================================================

set -euo pipefail

REPO="$HOME/Projects/cogames-autoresearch"
LOG="$REPO/autoresearch_loop.log"
PID_FILE="$REPO/autoresearch_loop.pid"
OPENCLAW_BIN="/opt/homebrew/bin/openclaw"
CLAUDE_BIN="$HOME/.local/bin/claude"
WHATSAPP_NUMBER="+12065321138"
CHECKPOINT_DIR="$REPO/checkpoints"
RESULTS_DIR="$REPO/results"
DISCUSSIONS_DIR="$REPO/discussions"
GH_REPO="SolbiatiAlessandro/cogames-autoresearch"
GH_DISCUSSION_CATEGORY="DIC_kwDORhT1Bs4C3_6L"  # "Show and tell"

AGENT_TIMEOUT=2400

cd "$REPO"
mkdir -p "$CHECKPOINT_DIR" "$RESULTS_DIR" "$DISCUSSIONS_DIR"

# =========================================================================
# Sync discussions from GitHub (so agent can read prior session reports)
# =========================================================================

sync_discussions() {
    log "Syncing discussions from GitHub..."
    gh api graphql -f query='
    {
      repository(owner: "SolbiatiAlessandro", name: "cogames-autoresearch") {
        discussions(first: 50, orderBy: {field: CREATED_AT, direction: DESC}) {
          nodes {
            number
            title
            body
            createdAt
            url
          }
        }
      }
    }' 2>/dev/null | python3 -c "
import json, sys, re, os
data = json.load(sys.stdin)
discussions_dir = '$DISCUSSIONS_DIR'
os.makedirs(discussions_dir, exist_ok=True)
for d in data['data']['repository']['discussions']['nodes']:
    num = d['number']
    title = d['title']
    body = d['body']
    created = d['createdAt'][:10]
    url = d['url']
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:60]
    filename = os.path.join(discussions_dir, f'{num:03d}-{slug}.md')
    with open(filename, 'w') as f:
        f.write(f'# {title}\n\n')
        f.write(f'**Discussion:** {url}\n')
        f.write(f'**Created:** {created}\n\n')
        f.write(body)
    print(f'  Synced: {filename}', file=sys.stderr)
" 2>&1 | while read line; do log "$line"; done
    log "Discussions synced."
}

# Sync prior session discussions from GitHub
sync_discussions

# =========================================================================
# Session setup: create a fresh branch (Karpathy pattern)
# =========================================================================

BASE_TAG=$(date '+%b%-d' | tr '[:upper:]' '[:lower:]')
RUN_TAG="$BASE_TAG"
SUFFIX=""
while git rev-parse --verify "autoresearch/$RUN_TAG" >/dev/null 2>&1; do
    if [[ -z "$SUFFIX" ]]; then
        SUFFIX="b"
    else
        SUFFIX=$(echo "$SUFFIX" | tr 'a-y' 'b-z')
    fi
    RUN_TAG="${BASE_TAG}${SUFFIX}"
done

BRANCH="autoresearch/$RUN_TAG"
RESULTS_FILE="$RESULTS_DIR/results_${RUN_TAG}.tsv"

# Make sure we're on main and up to date
git checkout main 2>/dev/null || true
git pull --rebase origin main 2>/dev/null || true

# Create the fresh session branch
git checkout -b "$BRANCH"

# Initialize session results file with header
echo -e "commit\tcomposite_score\tmean_reward\tmemory_gb\tstatus\tdescription\te2e_seconds\tapi_cost_usd\tcogs_junctions_held\tcogs_junctions_aligned\tclips_junctions_held\taligned_by_agent\tscrambled_by_agent\tcells_visited\tdeaths\tmove_success\tmove_failed\tvibe_changes\tcarbon_deposited\tcarbon_amount\toxygen_amount\tsilicon_amount\tgermanium_amount\theart_amount\tminer_gained\taligner_gained\tscrambler_gained\tscout_gained" > "$RESULTS_FILE"

# Also create/update the working results.tsv (what train.py writes to)
# Copy from results file so train.py appends here, then we sync back
cp "$RESULTS_FILE" "$REPO/results.tsv"

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

sync_results() {
    # Sync working results.tsv → session results file
    cp "$REPO/results.tsv" "$RESULTS_FILE"
}

# =========================================================================
# GitHub Discussion — session log
# =========================================================================

DISCUSSION_URL=""
DISCUSSION_NODE_ID=""

get_starting_context() {
    # Build the "starting from" context for the discussion
    local prev_best
    prev_best=$(tail -n+2 "$REPO/results.tsv" 2>/dev/null | sort -t$'\t' -k2 -rn | head -1 | cut -f6)
    local prev_score
    prev_score=$(get_best_score)

    cat << EOF
## Session: \`$RUN_TAG\`
**Branch:** \`$BRANCH\`
**Started:** $(date '+%Y-%m-%d %H:%M %Z')
**Starting from:** main @ \`$(git log --oneline -1 main 2>/dev/null)\`

### Starting state
- Previous best composite score: ${prev_score:-"none"}
- Best config: ${prev_best:-"none"}
- **Key problem:** composite_score is misleading — high scores (200+) come from reward hacking (agents farm resources, hold 0 territory). This session focuses on game metrics.

### Goals
- Get agents that actually play the game (junctions held > 0, aligned_by_agent > 0)
- Validate which reward combos produce real gameplay vs farming
- All experiments now log 20 game metrics alongside composite score

### Experiment log
| # | Score | Junctions | Aligned | Status | Description |
|---|------:|----------:|--------:|--------|-------------|
EOF
}

create_discussion() {
    local body
    body=$(get_starting_context)
    local title="Session $RUN_TAG — $(date '+%b %-d, %Y')"

    # Create discussion via GraphQL
    local repo_id
    repo_id=$(gh api graphql -f query="{ repository(owner:\"SolbiatiAlessandro\", name:\"cogames-autoresearch\") { id } }" -q '.data.repository.id')

    local result
    result=$(gh api graphql -f query="
mutation {
  createDiscussion(input: {
    repositoryId: \"$repo_id\",
    categoryId: \"$GH_DISCUSSION_CATEGORY\",
    title: \"$title\",
    body: $(echo "$body" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')
  }) {
    discussion {
      url
      id
    }
  }
}" 2>/dev/null) || true

    DISCUSSION_URL=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['createDiscussion']['discussion']['url'])" 2>/dev/null || echo "")
    DISCUSSION_NODE_ID=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['createDiscussion']['discussion']['id'])" 2>/dev/null || echo "")

    if [[ -n "$DISCUSSION_URL" ]]; then
        log "Created discussion: $DISCUSSION_URL"
        # Save this session's discussion to the discussions folder
        local disc_num
        disc_num=$(echo "$DISCUSSION_URL" | grep -oE '[0-9]+$' || echo "0")
        local disc_slug
        disc_slug=$(echo "$title" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]\+/-/g' | head -c 60)
        local disc_file="$DISCUSSIONS_DIR/$(printf '%03d' "$disc_num")-${disc_slug}.md"
        echo -e "# $title\n\n**Discussion:** $DISCUSSION_URL\n**Created:** $(date '+%Y-%m-%d')\n\n$body" > "$disc_file"
        git add "$disc_file" 2>/dev/null || true
    else
        log "Failed to create discussion (non-critical, continuing)"
    fi
}

update_discussion_body() {
    # Rebuild the full discussion body with current experiment table
    [[ -z "$DISCUSSION_NODE_ID" ]] && return

    local body
    body=$(get_starting_context)

    # Append experiment rows from this session's results
    local exp_num=0
    while IFS=$'\t' read -r commit score mean_reward mem status desc e2e cost jh ja ch aa sa rest; do
        [[ "$commit" == "commit" ]] && continue  # skip header
        exp_num=$((exp_num + 1))
        body+="| $exp_num | $score | ${jh:-?} | ${aa:-?} | $status | $desc |
"
    done < "$RESULTS_FILE"

    gh api graphql -f query="
mutation {
  updateDiscussion(input: {
    discussionId: \"$DISCUSSION_NODE_ID\",
    body: $(echo "$body" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')
  }) {
    discussion { url }
  }
}" >/dev/null 2>&1 || log "Failed to update discussion (non-critical)"
}

# =========================================================================
# Save PID, create discussion, announce
# =========================================================================

echo $$ > "$PID_FILE"

log "=========================================="
log "CoGames Autoresearch Loop v3 STARTING"
log "PID: $$"
log "Repo: $REPO"
log "Branch: $BRANCH (fresh session)"
log "Results: $RESULTS_FILE"
log "=========================================="

create_discussion

send_whatsapp "🧪 CoGames autoresearch session started — branch $BRANCH${DISCUSSION_URL:+ — $DISCUSSION_URL}"

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

    # === Clean train_dir ===
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

=== THIS SESSION'S RESULTS ===
$(cat results.tsv 2>/dev/null || echo 'no results yet')

=== CURRENT BEST SCORE: ${BEST_SCORE:-none} ===

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
    # CHECK FOR CREDIT EXHAUSTION
    # ===================================================================
    if echo "$AGENT_OUTPUT" | grep -qi "credit balance is too low\|insufficient credits\|billing\|rate limit.*exceeded\|quota exceeded"; then
        consecutive_credit_failures=$((consecutive_credit_failures + 1))
        log "⚠️ API CREDIT ISSUE detected (attempt $consecutive_credit_failures/3)"
        if [[ $consecutive_credit_failures -ge 3 ]]; then
            send_whatsapp "🛑 CoGames autoresearch ($BRANCH): API credits exhausted after $experiment_count experiments. Loop stopped.${DISCUSSION_URL:+ $DISCUSSION_URL}"
            log "API credits exhausted after 3 consecutive failures. Exiting."
            exit 1
        fi
        log "Retrying in 60 seconds..."
        sleep 60
        continue
    fi
    consecutive_credit_failures=0

    # Estimate API cost
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

    # === ARCHIVE CHECKPOINT ===
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
            send_whatsapp "🛑 CoGames autoresearch stopped after 3 critical blocks on $BRANCH.${DISCUSSION_URL:+ $DISCUSSION_URL}"
            log "Too many consecutive critical blocks. Exiting."
            exit 1
        fi
        log "Sleeping 5 minutes before retrying..."
        sleep 300
    else
        consecutive_crashes=0
        DONE_LINE=$(echo "$AGENT_OUTPUT" | grep "EXPERIMENT_DONE" | head -1 || echo "")
        log "Experiment #$experiment_count complete. $DONE_LINE"

        # Sync results to session file and update discussion
        sync_results
        update_discussion_body

        # Commit results file to branch
        cd "$REPO"
        git add "$RESULTS_FILE" results.tsv 2>/dev/null || true
        git commit -m "results: update after experiment #$experiment_count" --allow-empty 2>/dev/null || true

        # Sync to Notion
        bash "$REPO/sync_notion.sh" >> "$LOG" 2>&1 &

        # Push session branch
        git push -u origin "$BRANCH" >> "$LOG" 2>&1 || true

        log "Sleeping 10 seconds before next experiment..."
        sleep 10
    fi
done
