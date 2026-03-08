# cogames-autoresearch

Autonomous RL research on CoGames (Cogs vs Clips).

## Your task right now

Run the experiment loop below. NEVER stop and ask for confirmation. NEVER pause. NEVER wait for human input. Run experiments autonomously, one after another, forever.

## Setup (do this first)

```bash
cd ~/Projects/cogames-autoresearch
uv sync
```

Verify cogames is installed:
```bash
uv run python -c "import cogames; print('ok')"
```

If not found, install it:
```bash
uv pip install -e ~/Projects/cogames
```

## The experiment loop

LOOP FOREVER:

1. Read `results.tsv` and `git log --oneline -5` for context
2. Pick ONE thing to change in `train.py` (see ideas below)
3. Edit `train.py`, update `DESCRIPTION` to describe what you changed
4. `git add train.py && git commit -m "experiment: <short description>"`
5. `uv run train.py > run.log 2>&1`
6. Check results: `grep "^composite_score:\|^mean_reward:" run.log`
7. If empty or zero: `tail -50 run.log` (something crashed)
8. `cat results.tsv` to see logged row
9. If composite_score improved (higher than previous keep): leave commit as-is
10. If not improved: `git reset --hard HEAD~1`
11. Go to step 1

**Higher composite_score = better. Never stop.**

## What to change (start here, in this order)

### Experiment 1 — baseline (just run it, don't change anything)
- Keep train.py as-is, set `DESCRIPTION = "baseline lstm hidden=256"`
- Run and log the baseline score

### Experiment 2 — larger LSTM
- Change `HIDDEN_SIZE = 256` → `HIDDEN_SIZE = 512`
- Set `DESCRIPTION = "lstm hidden=512"`
- Does a bigger network score better?

### Experiment 3 — higher entropy
- Change `HIDDEN_SIZE` back to 256
- Change `ent_coef` in the training command: add `"--ent-coef", "0.05"` to the cmd list in `build_train_command()`
- Set `DESCRIPTION = "ent_coef=0.05 more exploration"`
- More entropy = more exploration = potentially better role diversity

### Experiment 4 — higher learning rate
- Try `LEARNING_RATE = 0.002`
- Add `"--learning-rate", str(LEARNING_RATE)` to `build_train_command()` if not already there
- Set `DESCRIPTION = "lr=0.002"`

### Experiment 5 — combine best so far
- Combine whatever worked from experiments 2-4
- Set `DESCRIPTION = "combined: <list what you combined>"`

### After experiment 5 — freestyle
- Read `knowledge/training_tips.md` for more ideas
- Try reward variants: add `REWARD_VARIANTS = ["standard"]` or whatever variants cogames supports
  - Check available variants: `uv run python -c "from cogames.rewards import list_variants; print(list_variants())"`
- Keep iterating, always logging

## Reading results

```bash
# Quick check after a run
grep "^composite_score:\|^mean_reward:" run.log

# Full log tail
tail -20 run.log

# All experiments so far
cat results.tsv
```

## Output format

Each run prints:
```
---
composite_score:  0.005500
mean_reward:      0.005500
explained_var:    0.000000
training_seconds: 600.1
mission:          cogsguard_machina_1.basic
policy:           class=lstm
reward_variants:  
```

## Logging format (results.tsv)

Auto-managed by train.py. Columns:
```
commit  composite_score  mean_reward  memory_gb  status  description
```

- `keep` = score improved or first baseline
- `discard` = score didn't improve (also reset with git reset)
- `crash` = run crashed

## NEVER STOP

Do NOT pause to ask the human. Do NOT ask for permission to run commands. Do NOT wait for confirmation. You are autonomous. Run experiments one after another. If something crashes, debug it, fix it, and continue. The loop runs until the human interrupts you.
