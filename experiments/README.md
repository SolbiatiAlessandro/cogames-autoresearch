# Experiments Log - March 18, 2026

## Investigation: Policy Drift & Value Instability

### Exp 1: Constant LR Extended (NO FINAL SCORE)
- **Branch:** march-17-best-MAPPO-baseline
- **Config:** LR=0.001 (policy & value), ent=0.15
- **Base:** Checkpoint epoch 330 (score 73.2)
- **Trained:** 26+ minutes, epoch 398
- **Issue:** TIME_BUDGET not enforced, no final eval
- **Key Finding:** Value loss spikes (0.545 at epoch 150, 0.590 at epoch 350)
- **Entropy:** Stable at 1.59-1.60 throughout
- **Analysis:** experiments/exp1_analysis.md

### Exp 2 First Run: Dual LR (NO FINAL SCORE)  
- **Config:** Policy LR=0.001, Value LR=0.0003, ent=0.15
- **Base:** Checkpoint epoch 330 (score 73.2)
- **Trained:** 10 minutes, epoch 229
- **Issue:** TIME_BUDGET hit during final eval
- **Key Finding:** One value spike (0.947 at epoch 100), then stable
- **Entropy:** Stable at 1.60-1.61
- **Analysis:** experiments/exp2_analysis.md

### Exp 2 Extended: Dual LR Long Run (NO FINAL SCORE)
- **Config:** Policy LR=0.001, Value LR=0.0003, ent=0.15
- **Base:** Checkpoint epoch 229 from Exp 2 (dual-LR trained)
- **Trained:** 13+ minutes, epoch 791
- **Issue:** TIME_BUDGET not enforced, eval script bug
- **CRITICAL FINDING:** Entropy collapsed 1.60 → 0.98 (40%) at epoch 200
- **Entropy recovery:** Settled at ~1.20 (never returned to 1.60)
- **Analysis:** experiments/exp2_extended_analysis.md

### Key Insights

1. **Value instability** (constant LR) → multiple spikes → bad advantages
2. **Dual LR fixes value** → stable after epoch 150
3. **BUT dual LR causes entropy collapse** → 1.60 → 1.20 → conservative play
4. **Entropy matters more than we thought** → even 25% drop (1.60→1.20) kills exploration

### Recommended Solution

**Population-Based Training (PBT)**
- Multiple agents with diverse LR/entropy settings
- Winners (high entropy + stable value) propagate
- Losers (low entropy or unstable) get replaced
- Natural selection for both stability AND exploration

See: EVOLUTIONARY_RL_PLAN.md

---

**Results without final scores logged in this README, not results.tsv**
