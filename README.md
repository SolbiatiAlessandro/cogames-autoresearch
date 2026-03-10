# cogames-autoresearch

![](https://github.com/SolbiatiAlessandro/cogames-autoresearch/blob/main/progress.png?raw=true)

Autonomous RL research on [CoGames](https://github.com/SolbiatiAlessandro/cogames) (Cogs vs Clips) using the [autoresearch](https://github.com/karpathy/autoresearch) pattern.

## Start a session

```bash
cd ~/Projects/cogames-autoresearch
claude --dangerously-skip-permissions
# then type: Follow program.md
```

That's it. Claude Code reads `program.md`, sets up a branch, reads prior session reports from [GitHub Discussions](https://github.com/SolbiatiAlessandro/cogames-autoresearch/discussions), and loops forever running experiments. Walk away, come back to results.

If the session dies (context window, crash), start a new one — it picks up from git log + results.tsv.

## How it works

1. Edit `train.py` with an experimental idea
2. `git commit`
3. `uv run train.py > run.log 2>&1` (10-minute time budget)
4. Check composite score AND game metrics (junctions held, agents aligning)
5. If genuine progress → keep. If reward hacking or worse → `git reset --hard HEAD~1`
6. Log to `results.tsv` (28 columns including 20 game metrics)
7. Repeat forever

Session reports are posted to [GitHub Discussions](https://github.com/SolbiatiAlessandro/cogames-autoresearch/discussions) — each session reads prior ones to build on past findings.

## File structure

```
cogames-autoresearch/
├── prepare.py          # READ-ONLY: env setup, evaluation harness, fixed metric
├── train.py            # AGENT EDITS: policy, hyperparams, reward variants, training loop
├── program.md          # HUMAN EDITS: research instructions, what to try/avoid
├── results.tsv         # Experiment log (auto-managed by agent)
├── results/            # Per-session results (results_mar7.tsv, etc.)
├── knowledge/          # Paper summaries, domain context, findings from prior sessions
│   ├── cogames_overview.md
│   ├── findings.md
│   ├── reward_variants.md
│   └── training_tips.md
└── checkpoints/        # Archived model checkpoints per experiment
```

## Prerequisites

- Python 3.12
- cogames package (`uv pip install -e ~/Projects/cogames`)
- GPU recommended (CUDA/MPS), CPU works but slow
- Claude Code CLI (`claude`)

## Credits

- Pattern: [karpathy/autoresearch](https://github.com/karpathy/autoresearch)
- Game: [Metta-AI/cogames](https://github.com/Metta-AI/cogames) (Softmax ALB)
