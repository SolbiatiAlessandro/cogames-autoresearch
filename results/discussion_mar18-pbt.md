## Session mar18-pbt — Mar 18, 2026

**Direction:** Implement Population-Based Training (PBT) to combat entropy collapse and policy drift in long runs. Prior experiments showed entropy degrading 1.60→0.98 in extended dual-LR runs (Exp2). PBT naturally selects for agents maintaining both value stability AND high entropy.

**Prior findings:**
- Best single-run score: 96b72bf = 69.7 (junctions=1029.8, 10min, gae=0.95)
- Best 20min run: ba53720 = 54.6 (junctions=541.2, BPTT=64 is the sweet spot)
- Problem: entropy collapses 1.60→0.98 in extended runs (Exp2 epoch 791)
- Dual LR (policy_lr/value_lr separate) partially helped but entropy still collapsed
- BPTT=64 > BPTT=128 > BPTT=16 for 20min runs (junction counts: 541 vs 162 vs 65)
- Base checkpoint: best_checkpoint/model_000330.pt (epoch 330, score ~73)

**Plan:**
1. PBT with 4 agents, 5 min/cycle, 4 cycles (~80 min total sequential)
2. Each agent gets random initial hyperparams (policy_lr, value_lr, entropy_coef, gae_lambda)
3. After each cycle: bottom 25% copy top 25%, all agents perturb ±20%
4. Goal: best agent maintains 73+ score after 30+ min (vs 58.6 baseline degradation)
5. Fixed BPTT=64 (sweet spot) + dual LR

**Experiment Log:** (to be filled as training runs)

**INFRA:** PBT manager created at pbt/manager.py. Runs via `uv run python pbt/manager.py`.
