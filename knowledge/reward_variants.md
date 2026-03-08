# CoGames Reward Variants Reference

The game has one true objective signal (junctions held per tick) plus stackable
shaping variants that add dense intermediate rewards.

## Available Variants

### `objective` (default)
- The base reward: aligned_junction_held per tick
- Sparse — only fires when territory is actually held
- Necessary but often insufficient alone for learning

### `milestones`
- Adds rewards for junction_scrambled_by_agent (weight 0.5) and
  junction_aligned_by_agent (weight 1.0)
- Directly rewards the territory-changing actions

### `milestones_2` (RECOMMENDED)
- Capped role-shaped rewards that favor alignment
- Scales up the objective reward by a compounding_factor (default 5.0)
- Custom factor: `milestones_2:25` (try different values!)
- Adds small rewards for:
  - Elements gained (miner incentive): weight 0.0015, max 3.0
  - Junction aligned (aligner incentive): weight 0.2, max 1.0
  - Hearts gained: weight 0.05, max 2.0
  - Junction scrambled: weight 0.1, max 1.0
- Key insight: the caps prevent farming single behaviors

### `credit`
- Dense precursor rewards for resource/gear acquisition:
  - heart_gained: 0.05 (cap 0.5)
  - aligner/scrambler gear gained/lost: ±0.2 (cap 0.4)
  - element gains (carbon, oxygen, germanium, silicon): 0.001 (cap 0.1)
- Helps bootstrap early learning but may limit final performance

### `role_conditional`
- Applies different shaping per agent based on their role assignment
- Requires per-agent configs (env.game.agents)
- Each role gets its own reward shaper (miner, aligner, scrambler, scout)

### Per-role variants: `miner`, `aligner`, `scrambler`, `scout`
- Apply a single role's shaping to ALL agents
- Useful for testing what a role-focused reward looks like

### `no_objective`
- Removes the base objective reward entirely
- Useful for testing whether shaping alone can drive learning

### `penalize_vibe_change`
- Small penalty (-0.01) for changing roles
- Discourages role-switching spam

## Stacking
Variants are stackable. Common combos:
- `milestones_2` — best standalone (recommended starting point)
- `milestones_2,credit` — dense + shaped (good for early experiments)
- `milestones_2:25` — aggressive compounding of objective reward
- `role_conditional` — per-agent role shaping (advanced)

## Key Insights
- The compounding factor in milestones_2 is the most important knob
- Dense rewards (credit) help early but may create local optima
- The caps in milestones_2 are carefully tuned to prevent farming
- Objective reward alone is too sparse for most architectures to learn from
