# cogames-autoresearch

Autonomous RL research on CoGames (Cogs vs Clips).

## Setup

To set up a new experiment session:

1. **Agree on a run tag**: propose a tag based on today's date (e.g. `mar7`). The branch `autoresearch/<tag>` must not already exist.
2. **Create the branch**: `git checkout -b autoresearch/<tag>` from current main.
3. **Read the in-scope files**: The repo is small. Read these files for full context:
   - `README.md` — repository context.
   - `prepare.py` — fixed constants, env setup, evaluation. **Do not modify.**
   - `train.py` — the file you modify. Policy, hyperparameters, reward variants, training loop.
   - `knowledge/` — domain context, reward variant docs, training tips.
4. **Verify cogames is installed**: `uv run python -c "import cogames; print('ok')"`. If not: `uv pip install -e ~/Projects/cogames`
5. **Initialize results.tsv**: Create with header row and baseline entry.
6. **Confirm and go**.

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

**The goal**: Get the highest `composite_score`. Higher = better (opposite of val_bpb).

**Simplicity criterion**: All else being equal, simpler is better. Removing code for equal results is a win.

**The first run**: Run train.py as-is to establish a baseline. Do not change anything.

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

## Logging results

Log to `results.tsv` (tab-separated):

```
commit	composite_score	mean_reward	memory_gb	status	description
```

- `keep` = score improved or baseline
- `discard` = score didn't improve (also `git reset --hard HEAD~1`)
- `crash` = run crashed (log 0.000000, then fix and retry)

## The experiment loop

LOOP FOREVER:

1. Look at git state: `git log --oneline -5` and `cat results.tsv`
2. Read `knowledge/` if you need ideas
3. Tune `train.py` with one experimental idea. Update `DESCRIPTION`.
4. `git add train.py && git commit -m "experiment: <description>"`
5. `uv run train.py > run.log 2>&1`
6. Read results: `grep "^composite_score:\|^mean_reward:" run.log`
7. If empty: run crashed. `tail -50 run.log` for the traceback. Fix and retry.
8. Log to results.tsv
9. If composite_score improved (higher): keep the commit
10. If equal or worse: `git reset --hard HEAD~1`
11. Go to 1

**NEVER STOP**: Do NOT pause to ask the human. Do NOT ask for confirmation. You are autonomous. If you run out of ideas, re-read `knowledge/`, combine near-misses, try radical changes. The loop runs until the human interrupts you.
