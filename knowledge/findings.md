# Session Findings — What We've Learned So Far

## Session: mar7 (March 7–8, 2026)

### The Big Discovery: role_conditional

`role_conditional` gives each agent a different reward function based on their assigned role
(miner, aligner, scrambler, scout). Without it, all agents share one reward and converge to
a mediocre generalist strategy. With it, score jumped from ~1.0 to 67.7 — a 67x leap.

### The Reward Stacking Progression

| Score | Config | What changed |
|------:|:-------|:-------------|
| 0.5 | milestones_2 | baseline — compounding rewards |
| 1.0 | milestones | direct junction rewards, no compounding |
| 67.7 | milestones + role_conditional | per-role rewards = specialization |
| 67.9 | + penalize_vibe_change | small stability bonus |
| 100.5 | + credit | dense resource pickup rewards |
| 234.0 | + scout | scout exploration rewards |

### ⚠️ THE REWARD HACKING PROBLEM

**The score of 234 is a lie.** When we watched the replay, agents are just walking around
collecting easy rewards. The game metrics tell the real story:

- `cogs_junctions_held`: **0** — our team holds ZERO territory
- `cogs_junctions_aligned`: **0** — we've captured ZERO junctions
- `clips_junctions_held`: **1,200,000** — the enemy holds EVERYTHING
- `aligned_by_agent`: **0** — no agent has ever aligned a junction
- `scrambled_by_agent`: **0** — no agent has ever scrambled a junction
- `miner/aligner/scrambler/scout_gained`: **~0** — agents aren't even picking up gear

**What agents ARE doing:** walking around (`cells_visited` = 3.3M), collecting solar energy,
picking up carbon from the ground. These behaviors give `credit` and `scout` reward points
but contribute nothing to actually winning the game.

**Why this happens:** The composite_score is `mean_reward`, which sums ALL variant rewards.
The `credit` variant gives +0.001 per element gained (carbon, oxygen, etc.) and the `scout`
variant rewards cell visitation. These fire thousands of times per episode. Meanwhile, the
actual game objective (aligning junctions) requires complex multi-step behavior: pick up
aligner gear → navigate to a junction → use the aligner. The easy rewards completely
dominate the signal.

### What This Means for Future Experiments

1. **Composite score alone is unreliable.** Always check the game metrics in results.tsv,
   especially `cogs_junctions_held` and `aligned_by_agent`.

2. **Adding more reward variants won't help if agents are already farming.** The problem
   isn't missing reward signal — it's that the easy signals drown out the hard ones.

3. **Promising directions:**
   - Reduce or remove `credit` and `scout` variants — they're the main source of farming
   - Increase weight of junction-related rewards relative to resource rewards
   - Try `milestones` + `role_conditional` without the noisy dense rewards
   - Try curriculum: first learn to pick up gear, THEN learn to use it
   - Increase entropy to prevent premature convergence on farming behavior
   - Try longer training — maybe 10 min is too short for the hard behaviors to emerge

4. **Hyperparameter tuning is premature.** Don't waste experiments on lr/gamma/gae tuning
   until agents are at least attempting to align junctions. Fix the reward signal first.

5. **A good experiment now:** one that gets `aligned_by_agent` > 0, even if composite_score
   drops significantly. That would be genuine progress.

### Dead Ends (don't retry these)

- `hidden_size=512`: regression, probably needs more training time
- `milestones_2` stacked with role_conditional: conflicting shaping signals
- `aligner` + `miner` added to winning combo: redundant with role_conditional
- `scrambler` added: marginal regression
- `gae_lambda=0.80` or `0.95`: both regressed
- `lr=0.0005`: too slow
- `no_objective + milestones`: catastrophic
- Longer training (1200s) with default LR schedule: actually scored lower (LR decays to 0)
