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
   - `knowledge/` — domain context, paper summaries, reward variant docs.
4. **Verify cogames is installed**: `cogames version`. If not, `pip install cogames` or `uv pip install -e ../cogames`.
5. **Initialize results.tsv**: Create `results.tsv` with header row and baseline entry.
6. **Confirm and go**: Confirm setup looks good.

Once you get confirmation, kick off the experimentation.

## Domain Context: Cogs vs Clips

Cogs vs Clips is a **multi-agent cooperative game** where a team of agents (Cogs) must capture and defend territory against automated opponents (Clips).

**Roles** (acquired at Gear Stations):
- **Miner**: +40 cargo, 10x resource extraction. Gathers resources for the team.
- **Aligner**: Captures neutral junctions using hearts. Expands territory.
- **Scrambler**: +200 HP, disrupts enemy junctions. Clears enemy territory.
- **Scout**: +100 energy, +400 HP, mobile reconnaissance. Explores the map.

**No single role can succeed alone.** Cooperation is required.

**Scoring**: Reward per tick = junctions_held / max_steps. More territory = more reward.

**The coordination problem**: Agents need to specialize into roles, gather resources, craft hearts, and capture junctions in a coordinated sequence. This is hard to learn from scratch.

## Experimentation

Each experiment runs the CoGames training loop for a **fixed time budget of 10 minutes** (wall clock). Launch: `uv run train.py > run.log 2>&1`

**What you CAN do:**
- Modify `train.py` — this is the only file you edit. Everything is fair game:
  - Reward variants (objective, milestones, milestones_2, credit, role_conditional)
  - Reward weights and caps
  - Policy architecture (hidden_size, use_rnn, n_layers)
  - Hyperparameters (learning_rate, gamma, gae_lambda, clip_coef, ent_coef)
  - Training loop structure
  - Minibatch size, number of environments

**What you CANNOT do:**
- Modify `prepare.py`. It is read-only.
- Modify the game rules or evaluation function.
- Install new packages not in `pyproject.toml`.

**The goal**: Get the highest composite_score. The composite score combines mean per-agent reward and coordination metrics. Higher = better.

**Simplicity criterion**: All else being equal, simpler is better. A small improvement that adds ugly complexity is not worth it. Removing code for equal results is a win.

## Output format

Once the script finishes it prints a summary:

```
---
composite_score:  0.123456
mean_reward:      0.234567
explained_var:    0.345678
training_seconds: 600.1
peak_vram_mb:     8192.0
mission:          cogsguard_machina_1.basic
policy:           class=lstm
reward_variants:  milestones_2
```

Extract the key metric: `grep "^composite_score:" run.log`

## Logging results

Log to `results.tsv` (tab-separated):

```
commit	composite_score	mean_reward	memory_gb	status	description
```

1. git commit hash (short, 7 chars)
2. composite_score (e.g. 0.123456) — use 0.000000 for crashes
3. mean_reward (e.g. 0.234567) — use 0.000000 for crashes
4. peak memory in GB (divide peak_vram_mb by 1024)
5. status: `keep`, `discard`, or `crash`
6. short text description of what this experiment tried

**Note**: Higher scores are BETTER (opposite of Karpathy's val_bpb where lower is better).

## The experiment loop

LOOP FOREVER:

1. Look at the git state and results.tsv for context
2. Read `knowledge/` if you need research ideas
3. Tune `train.py` with an experimental idea
4. git commit
5. Run: `uv run train.py > run.log 2>&1`
6. Read results: `grep "^composite_score:\|^mean_reward:\|^peak_vram_mb:" run.log`
7. If grep is empty, the run crashed. `tail -n 50 run.log` for the traceback.
8. Record results in results.tsv
9. If composite_score improved (higher), keep the commit
10. If score is equal or worse, `git reset --hard HEAD~1`

**Timeout**: Each experiment should take ~10 minutes. If a run exceeds 15 minutes, kill it and treat as failure.

**RL-specific guidance**:
- Reward shaping often matters MORE than architecture changes. Start with reward variants.
- milestones_2 is the current best reward variant. Try different compounding factors.
- Dense rewards (credit variant) help early learning but may limit final performance.
- Entropy coefficient controls exploration vs exploitation — critical for multi-agent RL.
- If agents aren't learning roles, the reward signal is probably too sparse.

**NEVER STOP**: Do NOT pause to ask the human. You are autonomous. If you run out of ideas, read the papers in `knowledge/`, re-read `prepare.py` for angles, try combining near-misses, try radical changes. The loop runs until the human interrupts you.
