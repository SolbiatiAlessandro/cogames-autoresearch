## Session mar17long — Mar 17, 2026

**Direction:** Longer training runs (20-30 min) on best junction configs. Build on PPO baseline improvements from prior sessions.

**Prior findings:**
- Best config: milestones_2:25 + role_conditional + penalize_vibe_change, ent=0.15, gamma=0.999, gae=0.95
- Best score: 69.7 (commit 96b72bf), junctions=1029.8 (10min run)
- heart_amount first appeared (1.8) in 12-march session with ent=0.10, 5min run
- Previous mar17 agent iterations timed out before completing training (setup took ~2300s of 2400s budget)

**Plan:**
1. Run best junction config at 20min (TIME_BUDGET=1200, lr=0.002) — done ✅
2. 20min with lr=0.001 (original LR, no scaling) — done ✅
3. 20-30min with BPTT variations — explored ✅
4. KEY FINDING: ba53720 (BPTT=64) got best 20min (541 junctions). All subsequent changes broke it.

**Experiment Log:**

### Exp 1: 20min, lr=0.002 (a803b76) — DISCARD
- score=47.7, junctions=329.8, clips dominating
- LR=0.002 too high → instability

### Exp 2: 20min, lr=0.001, BPTT=64 (ba53720) — KEEP ✅ BEST 20min
- score=54.6, junctions=541.2, aligned_by_agent=0.1
- BPTT=64 was the sweet spot for 20min

### Exp 3: 20min, lr=0.001, BPTT=128 (eb543ef) — DISCARD
- score=58.6, junctions=162.8 — BPTT=128 hurts 20min!

### Exp 4: 30min, lr=0.001, BPTT=128 (38ef2c2) — DISCARD
- score=68.5, junctions=151.8 — BPTT=128 still hurts at 30min

### Exp 5: 20min, lr=0.0015, BPTT=128 (4ae3c0b) — DISCARD
- score=52.9, junctions=122.1 — BPTT=128 + scaled LR even worse

### Exp 6: 20min, lr=0.001, BPTT=16 (928d515) — DISCARD
- score=36.6, junctions=65.8 — BPTT=16 worst yet!
- explained_variance ≈ 0 (value function not learning)

**Key Insight:** BPTT=64 is the sweet spot for 20min runs. BPTT=128 or BPTT=16 both hurt significantly.
**Next to try:** 30min run with BPTT=64, lr=0.001 — test if longer time helps when BPTT is right.

**INFRA:** Previous agents (iterations 1-2) timed out at 2400s loop limit because they spent ~2300s reading GitHub discussions and setting up before starting training. Fix: start training immediately, skip lengthy setup.

### Exp 7: 30min, lr=0.001, BPTT=64 (e7131d4) — DISCARD
- score=55.0, junctions=61.1, aligned_by_agent=0.1
- BPTT=64 at 30min overtrained dramatically: 541 → 61 junctions
- CONFIRMED: overtraining is NOT just a BPTT problem — 30min hurts even with optimal BPTT=64
- KEY FINDING: The sweet spot appears to be exactly 20min with BPTT=64 (ba53720). Longer = overtrained.
- Next direction: Address LR decay — default schedule decays to ~0 at 600s, so 20min only uses 50% of budget on active LR

### Exp 8: 20min, ent_coef=0.20, BPTT=64, lr=0.001 (c6c749e) — DISCARD
- score=60.3, cogs_junctions_held=0.0 (vs 541.2 baseline!), clips_junctions_held=1.19M
- CRITICAL FINDING: Higher entropy (0.20 vs 0.15) completely breaks junction holding — cogs get 0 junctions
- vibe_changes=0.0 (penalize still working), aligned_by_agent=0.0 (agents collecting gear but not aligning)
- Higher entropy doesn't help with overtraining — it disrupts the learned junction-holding behavior
- CONCLUSION: ent_coef=0.15 is REQUIRED for junction holding; do NOT increase entropy above 0.15
- Next direction: Try ent_coef=0.10 or 0.12 — could lower entropy improve junction focus at 20min?
  OR try vf_coef reduction to combat value function overfit at longer runs (alternate hypothesis)

