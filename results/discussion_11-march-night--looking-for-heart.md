## Session 11-march-night--looking-for-heart — Mar 11, 2026

**Direction:** Get agents to earn hearts. Hearts are the currency for junction alignment. The chain is: miners collect resources → deposit at base → assembler crafts hearts → aligners pick up hearts → spend on junction alignment. Previous sessions got miners picking up gear and depositing resources (carbon_deposited=2.5) but heart_amount=0.

**Prior findings:**
- Best known config: milestones_2 + role_conditional + penalize_vibe_change + miner + scout, ent_coef=0.05, vf_coef=4.0, bptt=128 → score=304, but heart_amount=0, aligned_by_agent=0
- Agents DO pick up gear (miner_gained=0.2, aligner_gained=0.2) and do deposit resources (carbon_deposited=2.5)
- Root cause of no-hearts: standalone `miner` variant (in REWARD_VARIANTS) sets heart_gained=-0.1 for ALL agents before role_conditional runs. Scout/scrambler agents end up with heart_gained=-0.1 — they're PUNISHED for hearts!
- Also `scout` + `miner` stacking creates conflicting penalties on each other's gear pickup
- `milestones_2` already rewards heart_gained via separate key `milestones2_heart_gained` (weight=0.05)
- `role_conditional` aligner correctly gets heart_gained=+0.5 (IF standalone miner variant doesn't interfere)
- Deposits at base: `_apply_miner` loss_diversity (weight=0.5, SUM_LOGS aggregation over all resource types) incentivizes depositing diverse resources

**Plan:**
1. Exp 1 (5 min / 300s): Clean setup — milestones_2:25 + role_conditional + penalize_vibe_change (NO standalone miner/scout). Higher entropy (ent_coef=0.1) to explore. Let role_conditional handle rewards cleanly. The aligner will have heart_gained=0.5, miner will have loss_diversity to incentivize deposits.
2. Exp 2 (10 min / 600s): If hearts > 0, scale up. Try milestones_2:50 for stronger territory signal.
3. Exp 3+ (20-30 min): Best config, longer training with proportionally higher LR.

**Experiment Log:** (to be filled)

**INFRA:** (fill only if something broke)
