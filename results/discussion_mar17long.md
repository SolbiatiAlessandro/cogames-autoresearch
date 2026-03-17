## Session mar17long — Mar 17, 2026

**Direction:** Longer training runs (20-30 min) on best junction configs. Build on PPO baseline improvements from prior sessions.

**Prior findings:**
- Best config: milestones_2:25 + role_conditional + penalize_vibe_change, ent=0.15, gamma=0.999, gae=0.95
- Best score: 69.7 (commit 96b72bf), junctions=1029.8
- 10min runs with this config were solid. Extended to 20min in commit 4940330 but agents timed out before logging.
- Previous two agent iterations (mar17 session) timed out at 2400s loop limit due to excessive setup time before training.

**Plan:**
1. Run the best junction config at 20min (TIME_BUDGET=1200, lr=0.002) — this is already configured in train.py
2. Longer training should let agents continue learning junction-holding behavior beyond 10min plateau
3. If successful, try 30min (TIME_BUDGET=1800) or try improving aligned_by_agent > 0

**Experiment Log:**
- (to be filled)

**INFRA:** Previous agents (iterations 1-2) timed out at 2400s loop limit because they spent ~2300s reading GitHub discussions and setting up before starting training. Fix: start training immediately, skip lengthy setup.
