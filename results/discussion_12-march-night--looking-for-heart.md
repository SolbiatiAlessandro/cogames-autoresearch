## Session 12-march-night--looking-for-heart — Mar 12, 2026

**Direction:** Get agents to earn hearts (heart_amount > 0) and align junctions (aligned_by_agent > 0). Hearts are the currency for junction alignment. Chain: miners collect resources → deposit at base → assembler crafts hearts → aligners pick up hearts → spend on junction alignment. Yesterday's session (11-march-night) crashed with OOM before any experiments ran. Today's session repeats that plan with OOM fix already in place (VECTOR_NUM_ENVS=64, VECTOR_NUM_WORKERS=8).

**Prior findings:**
- Best known config (mar7): milestones_2 + role_conditional + penalize_vibe_change + miner + scout, ent_coef=0.05, vf_coef=4.0, bptt=128 → score=304, but heart_amount=0, aligned_by_agent=0
- Deposits DO happen (carbon_deposited=2.5) but hearts NOT crafted → assembly chain broken
- ROOT CAUSE: standalone `miner` variant sets heart_gained=-0.1 for ALL agents (punishes scouts/scramblers for hearts). This blocks heart production.
- `role_conditional` CORRECTLY gives aligner heart_gained=+0.5 (IF standalone miner doesn't interfere)
- `milestones_2` rewards heart_gained via milestones2_heart_gained (weight=0.05) which also conflicts with miner penalty
- SOLUTION: Remove standalone miner/scout variants. Use clean milestones_2:25 + role_conditional + penalize_vibe_change only. Let role_conditional handle each agent's rewards properly.

**Plan:**
1. Exp 1 (5 min / 300s): Clean setup — milestones_2:25 + role_conditional + penalize_vibe_change (NO miner/scout). ent_coef=0.10 for more exploration. Target: heart_amount > 0.
2. Exp 2 (10 min): If hearts > 0, scale to milestones_2:50 and run longer.
3. Exp 3+ (20 min): Best config, longer training, proportionally higher LR (scale with TIME_BUDGET).
4. If hearts still 0 after exp 1: investigate deposit location vs assembly location, try miner variant only on miner role explicitly.

**Experiment Log:** (to be filled)

**INFRA:** OOM fix applied by Alessandro in commit 9dfaf64 (added VECTOR_NUM_ENVS=64, VECTOR_NUM_WORKERS=8 to train.py). CUDA A40 confirmed available. Session running on RunPod.
