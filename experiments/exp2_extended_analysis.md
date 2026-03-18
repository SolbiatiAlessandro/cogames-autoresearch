# Experiment 2 Extended Run - Accidental Discovery

## What Happened
TIME_BUDGET enforcement failed → training ran for 13+ minutes (epoch 791) instead of stopping at 10 min (epoch ~337).

**This is actually valuable data!** We can compare extended dual-LR training against the 30-min baseline.

## Training Metrics Progression

### Dual LR Extended (This Run)
| Epoch | Policy Loss | Value Loss | Entropy | Notes |
|-------|-------------|------------|---------|-------|
| 200   | 0.048       | 0.053      | **0.983** | ⚠️ ENTROPY COLLAPSED |
| 300   | 0.061       | 0.173      | **1.178** | Recovering |
| 400   | 0.064       | 0.144      | **1.056** | Still low |
| 500   | 0.058       | 0.157      | **1.325** | Better |
| 600   | 0.062       | 0.140      | **1.138** | Stable-ish |
| 700   | 0.049       | 0.112      | **1.181** | Good losses |
| 791   | 0.050       | 0.114      | **1.210** | End |

### Comparison: Exp 2 First Run (Dual LR, stopped at epoch 229)
| Epoch | Policy Loss | Value Loss | Entropy | Notes |
|-------|-------------|------------|---------|-------|
| 50    | 0.046       | 0.068      | **1.600** | Normal |
| 100   | -0.035      | 0.947      | **1.601** | Spike |
| 150   | 0.037       | 0.065      | **1.605** | Recovered |
| 200   | 0.042       | 0.063      | **1.604** | Stable |

### Comparison: Baseline 30-min (Constant LR)
| Epoch | Value Loss | Entropy | Notes |
|-------|------------|---------|-------|
| 337   | 0.035      | **1.603** | From 10-min run |
| 885   | 0.115      | **1.604** | From 30-min run |

## CRITICAL FINDING: Entropy Collapse! 🚨

**This run (dual LR) had DIFFERENT behavior:**

**Epochs 0-200:**
- Entropy: 1.60 → **0.98** (collapsed by 40%!)
- This is CATASTROPHIC for exploration
- Agent became deterministic/rigid

**Epochs 200-800:**
- Entropy recovered: 0.98 → 1.18-1.33
- But never returned to original 1.60
- Settled at ~1.20 (25% below baseline)

**Previous runs (constant LR):**
- Entropy stayed stable at 1.59-1.60 throughout
- NO collapse observed

## Why Did This Happen?

**Hypothesis:** The checkpoint we loaded was from epoch 229 of ANOTHER dual-LR run.

That run already had:
- Policy trained with dual LR for 229 epochs
- Value function 3x slower
- Potentially different entropy than baseline

When we loaded it and continued training:
1. Early epochs (200): System re-adjusting, entropy dropped
2. Mid epochs (300-500): Recovering equilibrium
3. Late epochs (600-800): Settled at new (lower) entropy

**This is DIFFERENT from:**
- Exp 1: Started from epoch 330 of constant-LR baseline → kept 1.60 entropy
- Exp 2 first run: Started from epoch 330 of baseline → kept 1.60 entropy
- This run: Started from epoch 229 of DUAL-LR run → entropy collapsed then recovered

## Implications

### The Good News ✅
- Value loss stayed stable (0.11-0.17) after epoch 300
- No massive spikes like Exp 1 (0.545, 0.590)
- Dual LR does stabilize value function

### The Bad News ❌
- **Entropy collapse is BAD**
- Low entropy = less exploration = conservative behavior
- This likely explains the performance drop we saw
- Agent became risk-averse (exactly what we DON'T want)

### The Mystery 🤔
- Why did entropy collapse with dual LR but not constant LR?
- Is it because:
  1. Slower value LR → worse advantage estimates → policy becomes deterministic?
  2. Loading checkpoint from dual-LR run → incompatible state?
  3. Dual LR fundamentally reduces exploration over time?

## Connection to Performance Degradation

**Remember:**
- 10-min baseline: Aggressive, high exploration → 73.2
- 30-min baseline: Conservative, less exploration → 58.6

**This run:**
- Entropy collapsed → deterministic policy → conservative behavior
- Likely score: Similar to 58.6 or worse

**The pattern:**
Longer training → lower effective exploration → conservative drift

**Even with stable value function, if entropy collapses, you still get:**
- Risk-averse behavior
- Fewer aggressive junction captures
- Letting enemies gain ground
- Performance drop

## What We Learned

1. **Dual LR stabilizes value function** ✅
   - No 0.5+ spikes
   - Steady 0.11-0.17 range

2. **BUT: Dual LR may cause entropy collapse** ❌
   - Dropped from 1.60 to 0.98
   - Recovered but stayed low (1.20)
   - This kills exploration

3. **Entropy is MORE IMPORTANT than we thought** 
   - Earlier we said "entropy was stable, not the problem"
   - BUT: Subtle 25% drop (1.60 → 1.20) might be enough
   - Need to maintain HIGH entropy for aggressive play

4. **Loading checkpoints from different training regimes is tricky**
   - Dual-LR checkpoint behaves differently than baseline checkpoint
   - State mismatch can cause instabilities

## Revised Recommendations

### Don't use dual LR alone
Instead, try:

1. **Entropy Schedule**
   - Start high (0.20) for exploration
   - Decay slowly to 0.15 over 500 epochs
   - Never go below 0.10

2. **Entropy-Regularized Dual LR**
   - Dual LR for value stability
   - PLUS explicit entropy bonus/penalty
   - Keep entropy above 1.50 threshold

3. **Population-Based Training (PBT)** ⭐ BEST OPTION
   - Multiple agents with different entropy coefficients
   - Winners (high entropy, aggressive) propagate
   - Losers (low entropy, conservative) get replaced
   - Natural selection for exploration

4. **Behavioral Cloning + Dual LR**
   - Dual LR for stability
   - BC loss toward aggressive checkpoint
   - Prevents both value instability AND entropy collapse

## Next Experiment

**Don't run more dual-LR experiments.** The issue is deeper:

**Problem hierarchy:**
1. Value instability → bad advantage estimates
2. Low entropy → conservative policy
3. Policy drift → forgets aggressive behaviors

**Dual LR only fixes #1.**

**Need a solution that addresses all three:**
→ **Population-Based Training** with entropy diversity

This naturally maintains:
- Stable value functions (through selection)
- High entropy agents (through diversity)
- Aggressive behaviors (through performance-based survival)

---

**Conclusion:** Dual LR is necessary but not sufficient. We need population-level dynamics to prevent both value instability AND exploration collapse.
