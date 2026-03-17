## Session mar17long — Mar 17, 2026

**Direction:** Longer training runs (20-30 min) on best junction configs. Build on PPO baseline improvements from prior sessions.

**Prior findings:**
- Best config: milestones_2:25 + role_conditional + penalize_vibe_change, ent=0.15, gamma=0.999, gae=0.95
- Best score: 69.7 (commit 96b72bf), junctions=1029.8
- heart_amount first appeared (1.8) in 12-march session with ent=0.10, 5min run
- Previous mar17 agent iterations timed out before completing training (setup took ~2300s of 2400s budget)

**Plan:**
1. Run best junction config at 20min (TIME_BUDGET=1200, lr=0.002) — already configured ✅
2. If worse due to high LR: try 20min with lr=0.001 (original LR, no scaling)
3. If 20min still worse: try 25-30min to see if longer horizon helps with junction holding
4. Always track heart_amount and aligned_by_agent for real game progress

**Experiment Log:**

### Exp 1: milestones_2:25 + role_cond + penalize_vibe, 20min, lr=0.002 (commit a803b76)
- composite_score: 47.7
- cogs_junctions_held: 329.8 | clips_junctions_held: 1,200,047 (clips dominating!)
- aligned_by_agent: 0.0 | heart_amount: 1.6
- **Status: DISCARD** — worse than best 10-min (69.7, junctions=1029.8)
- Diagnosis: LR=0.002 likely too high causing training instability in extended run. Clips team dominated.

**INFRA:** Previous agents (iterations 1-2) timed out at 2400s loop limit because they spent ~2300s reading GitHub discussions and setting up before starting training. Fix: start training immediately, skip lengthy setup. This allows ~1245s training + logging within 2400s loop budget.
