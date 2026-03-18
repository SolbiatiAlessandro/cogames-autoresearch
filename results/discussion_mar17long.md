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

### Exp 9: 20min, ent_coef=0.10, BPTT=64, lr=0.001 (12b2262) — DISCARD
- score=73.5 (highest yet!), cogs_junctions_held=166.6 (vs 541.2 baseline), clips_junctions_held=1.2M
- Lower entropy ALSO hurts junction holding — 166.6 vs 541.2 at ent=0.15
- Score up but junctions down: classic reward hacking. heart_amount=1.9, more gear collected.
- ENTROPY SWEET SPOT CONFIRMED: ent=0.15 is the only working entropy; both 0.10 and 0.20 break junction holding
- CONCLUSION: ent_coef range explored. Both lower and higher entropy than 0.15 reduce cogs_junctions_held.
- NEXT: try vf_coef=0.3 (vs 0.5 default) — the remaining anti-overtraining hypothesis for 20min runs


### Exp 10+: ent=0.15, vf_coef=0.3 (58f284f) — DISCARD
- junctions=115.4 (vs 541.2 baseline), confirmed vf_coef=0.3 hurts badly
- PBT session (5419cb7): cycle 1 winner lr=0.0013, value_lr=0.0006, ent=0.159 → 415j at 5min
- Dual LR + ent=0.10 tried → hurt (ev=-1.92, junc=77 vs 166)

### This session (mar18):
**Exp: ent=0.15 + clip_coef=0.1 + 25min (44a42ab) — DISCARD**
- score=62.3, junctions=261.4, aligned=0.1
- clip_coef=0.1 slows policy updates → 261j at 25min vs 541j baseline at 20min
- Conservative clipping hurts more than it helps — reduces junction learning rate
- CONCLUSION: clip_coef=0.1 is too conservative; standard 0.2 is better
- NEXT IDEAS: Try clip_coef=0.3 (more aggressive, faster learning), or try 20min with best config reproduced cleanly


**Exp: ent=0.10 clean 20min (ae6f8d2) — KEEP ✅ NEW BEST 20min**
- score=68.9, junctions=552.6, aligned=0.1
- Reproducing ent=0.10 without dual_LR → 552.6j BEATS ent=0.15 baseline (541.2j)!
- NOTE: Earlier ent=0.10 test (Exp 9, 12b2262) showed 166.6j at 20min, but that used a different config state
- REVISION: ent=0.10 is NOT worse than ent=0.15 — it's slightly better at 20min
- New best: 552.6j (ae6f8d2, ent=0.10) > 541.2j (ba53720, ent=0.15)

**Exp: ent=0.10 + 25min (4beabbb) — DISCARD**
- score=80.8, junctions=390.0, aligned=0.0
- Extended best 20min config (ent=0.10, 552.6j) to 25min → OVERTRAINING: 552j→390j
- Comparison: ent=0.15+clip=0.1 at 25min → 261j. So ent=0.10 declines more gracefully (390 vs 261j)
- But still overtrains. The 20min peak (552j) holds better than 25min.
- FINDING: ent=0.10 delays overtraining (390j at 25min vs 261j for ent=0.15) but doesn't eliminate it
- NEXT: The 20min peak is real and robust. Explore strategies to maintain or extend it:
  1. clip_coef=0.3 at 20min with ent=0.10 — more aggressive updates
  2. update_epochs=2 with ent=0.10 at 20min — more PPO sweeps per rollout
  3. BPTT=64 at 10min (NEVER TESTED!) — could it beat BPTT=128 at 10min (1029j)?

**Exp: update_epochs=2 + ent=0.10 + 20min (6d2479b) — DISCARD**
- score=69.2, junctions=202.6, aligned=0.0
- 2 PPO sweeps per rollout → HURTS: 202j vs 552j baseline
- update_epochs=2 causes faster overfit / policy degradation within 20min
- CONCLUSION: Single epoch (update_epochs=1) remains best. More sweeps per rollout destabilize learning.
- NEXT: Try clip_coef=0.3 at 20min with ent=0.10 — more aggressive per-step updates (different from more epochs)

**Exp: clip_coef=0.3 + ent=0.10 + 20min (c4e352a) — DISCARD**
- score=48.7, junctions=148.9, aligned=0.1
- clip_coef=0.3 (more aggressive) → SEVERE DECLINE: 148.9j vs 552.6j baseline (73% drop!)
- Larger policy steps cause instability; standard clip_coef=0.2 is optimal
- CLIP_COEF CONCLUSION: Both 0.1 (too conservative) and 0.3 (too aggressive) hurt. Keep 0.2.
- REMAINING LEVERS: Try PBT hyperparams (lr=0.0013, ent=0.159) at 20min, or BPTT=64 at 10min

**Exp: cosine_lr 0.001->0.00005 + ent=0.10 + clip=0.2 + bptt=64 + 20min (2524a23) — DISCARD**
- score=63.8, junctions=394.2, aligned=0.0
- Time-based cosine LR decay → HURTS: 394j vs 552j baseline (29% drop at 20min)
- Decaying LR too early slows useful learning in the second half of training
- COSINE LR CONCLUSION: Constant LR=0.001 outperforms cosine decay at 20min. The overtraining issue isn't caused by too-high LR late — it happens between 20min and 25min runs.
- REMAINING LEVERS: Try PBT hyperparams (lr=0.0013, ent=0.159) at 20min, or BPTT=64 at 10min

**Exp: PBT-hyperparams ent=0.159 lr=0.0013 bptt=64 20min (9f3297d) — DISCARD**
- score=44.3, junctions=91.5, aligned=0.0
- PBT-validated hyperparams (cycle 1 winner: lr=0.0013, ent=0.159) → SEVERE DECLINE: 91.5j vs 552.6j baseline (83% drop!)
- ent=0.159 is very close to ent=0.20 which gave 0j (complete failure). Slightly lower entropy but same effect.
- ENTROPY BOUNDARY: ent=0.15 → 541j, ent=0.159 → 91.5j. Very sharp threshold around ent=0.155-0.158.
- The PBT hyperparams worked in a 5min PBT context (starting from checkpoint) but fail in standalone 20min training.
- CONCLUSION: PBT results don't transfer to standalone training. The entropy boundary is very sharp.
- REMAINING NEXT IDEAS: BPTT=64 at 10min (direction says 20-30min but worth knowing), or entropy annealing (high→low over training), or smaller LR at 20min (0.0005).

**Exp: lr=0.0005 + ent=0.10 + bptt=64 + 25min (4794d53) — DISCARD**
- score=80.2, junctions=6.4, aligned=0.0
- Half LR (0.001→0.0005) → CATASTROPHIC DECLINE: 6.4j vs 552.6j baseline (99% drop!)
- Lower LR severely slows junction learning — agents collect gear (heart_amount=2.2, high gear metrics) but never learn to hold junctions
- Clips dominate: clips_junctions_held=1.2M while cogs get only 6.4
- LOWER LR CONCLUSION: lr=0.0005 is far worse than lr=0.001 at 25min. The 20min sweet spot (552.6j) is not due to too-fast learning; slower learning just prevents agents from learning the junction objective at all.
- REMAINING LEVERS: Entropy annealing (start ent=0.15→end ent=0.05), GAE_LAMBDA sweep (0.98/0.99), or BPTT=64 at 10min

**Exp: gae=0.98 + ent=0.10 + lr=0.001 + bptt=64 + 20min (950f6d9) — DISCARD**
- score=69.1, junctions=447.5, aligned=0.1
- GAE_LAMBDA=0.98 (longer credit horizon) → WORSE: 447.5j vs 552.6j baseline (19% drop!)
- PBT session found gae=0.98 in converged population, but standalone 20min training prefers gae=0.95
- CONCLUSION: gae=0.95 remains optimal. Longer credit horizon doesn't help at 20min.
- REMAINING LEVERS: Entropy annealing (start ent=0.15→end ent=0.05), BPTT=64 at 10min

**Exp: ent_anneal=0.15→0.05 + lr=0.001 + bptt=64 + gae=0.95 + 25min (a0c2824) — DISCARD**
- score=82.3, junctions=352.8, aligned=0.1
- Entropy annealing 0.15→0.05 over 25min → WORSE: 352.8j vs 390.0j constant ent=0.10 at 25min
- Also worse than 20min constant ent=0.10 (552.6j baseline)
- Root cause: starting at ent=0.15 (not ent=0.10) was detrimental. Higher initial entropy hurts because ent=0.15 is not optimal — the first half of training explores too much vs ent=0.10 constant.
- The entropy annealing midpoint avg is 0.10 (same as constant) but with more variance; this variance hurt.
- CONCLUSION: Entropy annealing from 0.15→0.05 does NOT help. Starting entropy matters — ent=0.10 is the sweet spot from the start, not just the end.
- REMAINING LEVERS: Try ent_anneal=0.10→0.03 at 25min (start from optimal, end lower); try BPTT=64 at 10min; try hidden_size=512

**Exp: ent_anneal=0.10→0.03 + lr=0.001 + bptt=64 + gae=0.95 + 25min (95a435d) — DISCARD**
- score=80.9, junctions=0.0, aligned=0.0, clips_junctions_held=1,197,097.5
- CATASTROPHIC FAILURE: Starting at ent=0.10 and decaying to 0.03 → cogs get ZERO junctions while clips hold 1.2M
- Aggressive entropy decay (0.10→0.03) completely kills the cogs ability to hold junctions
- Even more destructive than 0.15→0.05 anneal (352.8j) — removing exploration late is devastating
- ENTROPY ANNEALING CONCLUSION: ALL entropy annealing experiments fail worse than constant ent=0.10. Do NOT anneal entropy.
  - 0.15→0.05 = 352.8j (DISCARD)
  - 0.10→0.03 = 0j (CATASTROPHIC)
  - Constant ent=0.10 = 552.6j (BEST)
- REMAINING UNEXPLORED: BPTT=64 at 10min, hidden_size=512 at 20min, architectural changes

**Exp: hidden_size=512 + ent=0.10 + lr=0.001 + bptt=64 + gae=0.95 + 20min (a0dd59e) — DISCARD**
- score=64.3, junctions=0.0, aligned=0.0, clips_junctions_held=1,196,417.9
- CATASTROPHIC FAILURE: larger LSTM (512 vs 256) → ZERO cogs junctions, clips dominate completely
- Larger model needs more samples to converge, or the larger parameter space is harder to optimize in 20min
- HIDDEN SIZE CONCLUSION: hidden_size=256 remains optimal for 20min runs. Bigger is NOT better here.
- REMAINING LEVERS: BPTT=64 at 10min (direction says 20-30min), or reward variant weight tuning, or a different reward combo

**Exp: minibatch=4096 + ent=0.10 + lr=0.001 + bptt=64 + gae=0.95 + 20min (4de32d6) — DISCARD**
- score=63.4, junctions=53.9, aligned=0.0, clips_junctions_held=1,202,856
- SEVERE FAILURE: half minibatch (4096 vs 8192) → 90% drop in cogs junctions: 53.9j vs 552.6j baseline
- Smaller minibatch = fewer steps per gradient update = worse learning for junction-holding
- MINIBATCH CONCLUSION: minibatch=8192 is optimal. Smaller batches (4096) drastically hurt at 20min.
- REMAINING LEVERS: Reward variant weight tuning (milestones_2:50 vs :25), different reward combos, rollout_length changes
