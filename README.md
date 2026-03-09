# cogames-autoresearch

![](https://github.com/SolbiatiAlessandro/cogames-autoresearch/blob/main/progress.png?raw=true)

Autonomous RL research on [CoGames](https://github.com/SolbiatiAlessandro/cogames) (Cogs vs Clips) using the [autoresearch](https://github.com/karpathy/autoresearch) pattern.

## How it works

An AI agent (Claude Code / OpenCode) runs in an infinite loop:

1. Edit `train.py` with an experimental idea
2. `git commit`
3. `uv run train.py > run.log 2>&1` (10-minute time budget)
4. Check results: `grep "^composite_score:" run.log`
5. If improved → keep. If not → `git reset --hard HEAD~1`
6. Log to `results.tsv`
7. Repeat forever

## File structure

```
cogames-autoresearch/
├── prepare.py          # READ-ONLY: env setup, evaluation harness, fixed metric
├── train.py            # AGENT EDITS: policy, hyperparams, reward variants, training loop
├── program.md          # HUMAN EDITS: research instructions, what to try/avoid
├── results.tsv         # Experiment log (auto-managed by agent)
├── knowledge/          # Paper summaries, domain context (agent reads for ideas)
│   ├── cogames_overview.md
│   ├── reward_variants.md
│   └── training_tips.md
└── README.md           # This file
```

## Quick start

```bash
# Prerequisites: cogames installed (pip install cogames or from ../cogames)
uv sync

# Run one training experiment manually
uv run train.py

# Start the autonomous loop (point Claude Code at program.md)
# Or use Ralph Loop for overnight runs
```

## Prerequisites

- Python 3.12
- cogames package (from `../cogames` or PyPI)
- GPU recommended (CUDA), CPU works but slow
- For autonomous loop: Claude Code CLI or OpenCode

## Research directions

See `knowledge/` for domain context and `program.md` for the full experiment protocol.

Current focus areas:
1. **Reward shaping**: Which reward variants produce the best coordination?
2. **Architecture**: Does network size / LSTM matter for role specialization?
3. **Intrinsic rewards**: Can social influence or phase synchronization bootstrap coordination?

## Credits

- Pattern: [karpathy/autoresearch](https://github.com/karpathy/autoresearch)
- Game: [Metta-AI/cogames](https://github.com/Metta-AI/cogames) (Softmax ALB)
