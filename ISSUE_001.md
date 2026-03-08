# Issue #1: First end-to-end experiment run

## Goal
Run `cogames tutorial train` with the LSTM policy from within `cogames-autoresearch`, and log the result to `results.tsv`.

## Success State ✅
All of the following must be true:

1. `uv run train.py` executes successfully from the `cogames-autoresearch/` directory
2. It runs `cogames tutorial train -m cogsguard_machina_1.basic -p class=lstm` for the configured time budget
3. After training completes, a checkpoint exists in `./train_dir/`
4. The script prints the standard output format:
   ```
   ---
   composite_score:  <number>
   mean_reward:      <number>
   training_seconds: <number>
   ...
   ```
5. A row is logged to `results.tsv` with: commit hash, composite_score, mean_reward, memory_gb, status (keep), description ("baseline")
6. `grep "^composite_score:" run.log` returns a non-zero value

## Steps
1. [ ] `uv sync` resolves all dependencies (cogames + torch)
2. [ ] `uv run train.py` launches cogames training via subprocess
3. [ ] Training respects TIME_BUDGET (stops after 10 min)
4. [ ] Script finds the latest checkpoint in `./train_dir/` after training
5. [ ] Script extracts metrics from training output (mean_reward, explained_variance)
6. [ ] Script prints results in standard format
7. [ ] Manually log baseline to `results.tsv`

## Not in scope
- Evaluation function (prepare.py evaluate()) — that's a separate issue
- Ralph Loop / autonomous looping — just one manual run
- GPU — can test on CPU first (slow but functional)

## Notes
- The cogames tutorial was confirmed working on this machine
- Dependencies: cogames needs Python 3.12, mettagrid, pufferlib-core
- On Mac (MPS or CPU), training will be slow but should work
