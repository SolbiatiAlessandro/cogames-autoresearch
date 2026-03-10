# cogames-autoresearch

Autonomous RL research on CoGames (Cogs vs Clips). You are a fully autonomous researcher. There is no human to talk to. You will not receive replies. You run experiments in a loop until you are interrupted.

The human starts you with a message like: `branch: mar10-anti-farming | direction: remove credit and scout, focus on milestones_2 with caps to prevent reward hacking`. That message is your research brief. The branch name and the direction guide your experiments for the entire session.

## Setup (do this ONCE at the start)

1. **Parse the human's starting message** for the branch name and research direction. These are your instructions for the session.
2. **Create the branch**: `git checkout -b autoresearch/<branch_name>` from current main.
3. **Read prior session reports from GitHub Discussions**:
   ```bash
   gh api graphql -f query='{ repository(owner:"SolbiatiAlessandro", name:"cogames-autoresearch") { discussions(first:20, orderBy:{field:CREATED_AT, direction:DESC}) { nodes { number title body } } } }' -q '.data.repository.discussions.nodes[] | "## #\(.number): \(.title)\n\(.body)\n---"'
   ```
   Each discussion is a session report from a prior run with findings, dead ends, and ideas. Read ALL of them. Build on their insights. Don't repeat their mistakes.
4. **Read the repo files**:
   - `prepare.py` — fixed evaluation harness. **Do not modify.**
   - `train.py` — the ONE file you edit.
   - `knowledge/` — domain context, reward variant docs, `findings.md`.
   - `results/` — per-session results files from prior runs.
5. **Verify cogames is installed**: `uv run python -c "import cogames; print('ok')"`. If not: `uv pip install -e ~/Projects/cogames`
6. **Create a GitHub Discussion** for this session:
   ```bash
   gh discussion create --repo SolbiatiAlessandro/cogames-autoresearch \
     --category "Show and tell" \
     --title "Session <branch_name> — $(date '+%b %-d, %Y')" \
     --body "<starting context: direction, what you read from prior discussions, your plan>"
   ```
   This discussion is your session log. It will be read by future sessions.
7. **Initialize results.tsv** with the header row (see Logging section).
8. **Start the experiment loop.**

## The experiment loop

LOOP FOREVER:

1. **Think**: look at `git log --oneline -5` and `cat results.tsv`. What should you try next, given the research direction?
2. **Edit** `train.py` with one experimental idea. Update `DESCRIPTION`.
3. **Commit**: `git add train.py && git commit -m "experiment: <description>"`
4. **Run**: `uv run train.py > run.log 2>&1`
5. **Check results**:
   - `grep "^composite_score:\|^mean_reward:" run.log`
   - `grep -A20 "Game Metrics" run.log` — are agents actually playing the game?
   - If empty → crash. `tail -50 run.log`, fix, retry up to 2 times.
6. **Log** to results.tsv (train.py auto-appends most columns; you fill in session_tokens_cumulative and session_cost_cumulative — see Logging section).
7. **Decide**:
   - Genuine game progress (junctions held, aligned_by_agent > 0) → **keep**
   - Score up but game metrics flat/zero → reward hacking → **discard** + `git reset --hard HEAD~1`
   - Equal or worse → **discard** + `git reset --hard HEAD~1`
8. **Push**: `git push -u origin autoresearch/<branch_name>`
9. **Update the GitHub Discussion** if you made an interesting finding (not every experiment — only when something noteworthy happened: a breakthrough, a surprising failure, a new insight). Keep the discussion concise and useful for future sessions.
10. Go to 1.

**NEVER STOP.** Do not pause to ask questions. There is no human listening. You are autonomous. If you run out of ideas, re-read the GitHub Discussions and `knowledge/`, combine near-misses, try radical changes. The loop runs until the human kills your process.

## What you CAN and CANNOT do

**CAN**: Modify `train.py` — everything is fair game: policy architecture, hyperparameters, reward variants, training loop.

**CANNOT**: Modify `prepare.py`. Install new packages. Stop to ask questions.

## ⚠️ What "Better" means

**DO NOT blindly optimize composite_score.** It sums ALL reward variant signals and is easily gamed — agents score 200+ by collecting resources while holding ZERO territory.

**The REAL goal is agents that play the game.** The key metrics:

- `cogs_junctions_held` — territory held (THE ACTUAL GAME OBJECTIVE)
- `aligned_by_agent` — did any agent align a junction?
- `scrambled_by_agent` — did any agent scramble?
- `miner_gained`, `aligner_gained`, `scrambler_gained`, `scout_gained` — gear pickups

**An experiment with aligned_by_agent > 0 and score 10 beats one with score 300 and zero junctions.**

## Logging results

`results.tsv` is tab-separated. train.py auto-appends most columns when it runs. You are responsible for filling in the cost tracking columns.

**Header:**
```
commit	composite_score	mean_reward	memory_gb	status	description	timestamp	e2e_seconds	session_tokens_cumulative	session_cost_cumulative	cogs_junctions_held	cogs_junctions_aligned	clips_junctions_held	aligned_by_agent	scrambled_by_agent	cells_visited	deaths	move_success	move_failed	vibe_changes	carbon_deposited	carbon_amount	oxygen_amount	silicon_amount	germanium_amount	heart_amount	miner_gained	aligner_gained	scrambler_gained	scout_gained
```

**Cost tracking columns (your responsibility):**
- `session_tokens_cumulative` — your running total of tokens used in this session. Check with `/cost`.
- `session_cost_cumulative` — your running total dollar cost. Sonnet pricing: $3/M input, $15/M output.

**Status values:** `keep`, `discard`, `crash`

## Commit messages

Include: (1) what you changed, (2) game metrics summary, (3) your assessment.

Example: `experiment: milestones_2 + role_conditional — junctions_held=500, aligned=3, real progress`

## Training time

Default TIME_BUDGET is 600s (10 min). Override in train.py:
```python
import prepare; prepare.TIME_BUDGET = 1200  # 20 min
```
**If you increase TIME_BUDGET, also increase the learning rate** — the default LR schedule decays to near-zero at 600s.

## Checkpoints

Archived to `checkpoints/<commit_hash>/model_final.pt`. Replay:
```
cogames play -m cogsguard_machina_1.basic -p class=lstm,data=checkpoints/<commit>/model_final.pt --autostart
```
