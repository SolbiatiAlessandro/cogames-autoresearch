# cogames-autoresearch

Autonomous RL research on CoGames (Cogs vs Clips).

## Setup

To set up a new experiment session:

1. **Agree on a run tag**: propose a tag based on today's date (e.g. `mar7`). The branch `autoresearch/<tag>` must not already exist.
2. **Create the branch**: `git checkout -b autoresearch/<tag>` from current main.
3. **Read prior session reports from GitHub Discussions**:
   ```bash
   gh api graphql -f query='{ repository(owner:"SolbiatiAlessandro", name:"cogames-autoresearch") { discussions(first:20, orderBy:{field:CREATED_AT, direction:DESC}) { nodes { number title body } } } }' -q '.data.repository.discussions.nodes[] | "## #\(.number): \(.title)\n\(.body)\n---"'
   ```
   **This is the most important context.** Each discussion is a session report from a prior run — it contains findings, dead ends, and next-step ideas. Read ALL of them. Build on their insights, don't repeat their mistakes.
4. **Read the in-scope files**: The repo is small. Read these files for full context:
   - `README.md` — repository context.
   - `prepare.py` — fixed constants, env setup, evaluation. **Do not modify.**
   - `train.py` — the file you modify. Policy, hyperparameters, reward variants, training loop.
   - `knowledge/` — domain context, reward variant docs, training tips, **and findings.md (CRITICAL)**.
   - `results/` — per-session results files (results_mar7.tsv, etc.). Skim for raw data behind the discussion findings.
5. **Verify cogames is installed**: `uv run python -c "import cogames; print('ok')"`. If not: `uv pip install -e ~/Projects/cogames`
6. **Initialize results.tsv**: Create with header row and baseline entry.
7. **Confirm and go**.

Once setup is confirmed, kick off the experimentation.

## Experimentation

Each experiment runs for a **fixed time budget of 10 minutes** (wall clock). Launch: `uv run train.py > run.log 2>&1`

**What you CAN do:**
- Modify `train.py` — this is the only file you edit. Everything is fair game:
  - Policy architecture (hidden_size, LSTM vs stateless, n_layers)
  - Hyperparameters (learning_rate, gamma, gae_lambda, clip_coef, ent_coef, minibatch_size)
  - Reward variants (REWARD_VARIANTS list)
  - Training loop structure

**What you CANNOT do:**
- Modify `prepare.py`. It is read-only.
- Install new packages not in `pyproject.toml`.

## ⚠️ CRITICAL: What "Better" Means

**DO NOT blindly optimize composite_score.** The composite score is just `mean_reward`, which sums ALL reward variant signals. This is **easily gamed** — agents can score 200+ by walking around collecting resources while holding ZERO territory.

**The REAL goal is agents that play the game well.** Check the game metrics in results.tsv after EVERY experiment:

- `cogs_junctions_held` — how much territory our team holds (THIS IS THE ACTUAL GAME OBJECTIVE)
- `cogs_junctions_aligned` — junctions we've captured
- `aligned_by_agent` — did any agent actually align a junction?
- `scrambled_by_agent` — did any agent scramble enemy junctions?
- `miner_gained`, `aligner_gained`, `scrambler_gained`, `scout_gained` — are agents picking up gear?

**An experiment that gets `aligned_by_agent > 0` with a composite_score of 10 is MORE VALUABLE than one that scores 300 with zero junctions held.**

After each run, write a brief comment in your commit message about what the game metrics showed — not just the score.

## Output format

```
---
composite_score:  0.005500
mean_reward:      0.005500
explained_var:    0.000000
training_seconds: 600.1
peak_vram_mb:     0.0
mission:          cogsguard_machina_1.basic
policy:           class=lstm
reward_variants:  
```

Extract the key metric: `grep "^composite_score:" run.log`

**Also check game metrics**: `grep -A20 "Game Metrics" run.log`

## Logging results

Log to `results.tsv` (tab-separated). The file has 28 columns including game metrics:

```
commit	composite_score	mean_reward	memory_gb	status	description	e2e_seconds	api_cost_usd	cogs_junctions_held	cogs_junctions_aligned	clips_junctions_held	aligned_by_agent	scrambled_by_agent	cells_visited	deaths	move_success	move_failed	vibe_changes	carbon_deposited	carbon_amount	oxygen_amount	silicon_amount	germanium_amount	heart_amount	miner_gained	aligner_gained	scrambler_gained	scout_gained
```

**ALL columns must be populated.** train.py logs them automatically — verify they appear in run.log output. If game metrics are all 0.0, something is wrong with metric extraction.

- `keep` = experiment shows genuine progress (check game metrics, not just score)
- `discard` = no improvement or reward hacking (also `git reset --hard HEAD~1`)
- `crash` = run crashed (log 0.000000, then fix and retry)

## Commit messages

Every commit message MUST include:
1. The experiment description (reward variants + hyperparameter changes)
2. A brief note on game metrics: e.g. "junctions_held=1200, aligned=5" or "still 0 junctions"
3. Your assessment: is this real progress or reward hacking?

Example: `experiment: milestones_2 + role_conditional — junctions_held=500, aligned=3, real progress`

## The experiment loop

LOOP FOREVER:

1. Look at git state: `git log --oneline -5` and `cat results.tsv`
2. **Fetch and read GitHub Discussions** for prior session findings (see Setup step 3)
3. **Read `knowledge/findings.md`** for detailed reward hacking analysis
4. Read `knowledge/` if you need more domain context
5. Tune `train.py` with one experimental idea. Update `DESCRIPTION`.
6. `git add train.py && git commit -m "experiment: <description>"`
7. `uv run train.py > run.log 2>&1`
8. Read results: `grep "^composite_score:\|^mean_reward:" run.log`
9. **Check game metrics**: `grep -A20 "Game Metrics" run.log` — are agents actually playing?
10. If empty: run crashed. `tail -50 run.log` for the traceback. Fix and retry.
11. Log to results.tsv (train.py does this automatically)
12. If experiment shows **genuine game progress** (higher junctions_held, aligned_by_agent > 0): keep
13. If score went up but game metrics are flat/zero: this is reward hacking, discard
14. If equal or worse on both score AND game metrics: `git reset --hard HEAD~1`
15. Go to 1

**NEVER STOP**: Do NOT pause to ask the human. Do NOT ask for confirmation. You are autonomous. If you run out of ideas, re-read the GitHub Discussions and `knowledge/`, combine near-misses, try radical changes. The loop runs until the human interrupts you.

## Checkpoints

After each experiment, the best checkpoint is archived to `checkpoints/<commit_hash>/model_final.pt`.
To replay any experiment:
```
cogames play -m cogsguard_machina_1.basic -p class=lstm,data=checkpoints/<commit>/model_final.pt --autostart
```

## Training Time

Default TIME_BUDGET is 600s (10 min). The agent may increase it by monkey-patching in train.py:
```python
import prepare; prepare.TIME_BUDGET = 1200  # 20 min
```

Available budgets: 600s (default), 1200s (20 min), 1800s (30 min).

**Important**: If you increase TIME_BUDGET, also rescale the learning rate schedule. The default
schedule decays LR to near-zero at 600s — longer runs with the default schedule just grind at
zero LR. Consider increasing the base LR proportionally or using a cosine schedule with proper
warmdown fraction.
