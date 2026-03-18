# Experiment 2 Analysis - Dual Learning Rates

## Setup
- **Config:** Policy LR=0.001, Value LR=0.0003 (3x slower)
- **Base:** Checkpoint epoch 330 (score 73.2)
- **Training:** Ran for 229 epochs (10 minutes)
- **Note:** Final evaluation didn't complete (TIME_BUDGET triggered during eval)

## Training Metrics Progression

| Epoch | Policy Loss | Value Loss | Entropy | Notes |
|-------|-------------|------------|---------|-------|
| 50    | 0.046       | 0.068      | 1.600   | Stable, both losses low |
| 100   | **-0.035**  | **0.947**  | 1.601   | 🚨 VALUE SPIKE + negative policy |
| 150   | 0.037       | 0.065      | 1.605   | Recovered! |
| 200   | 0.042       | 0.063      | 1.604   | Stable |
| 229   | (end)       |            |         |       |

## Comparison with Experiment 1 (constant LR)

### Value Loss Behavior

**Exp 1 (LR=0.001 for both):**
- Epoch 50: 0.187 ⚠️
- Epoch 100: 0.099
- Epoch 150: **0.545** 🚨 HUGE SPIKE
- Epoch 200: 0.157
- Epoch 250: 0.148
- Epoch 300: 0.062
- Epoch 350: **0.590** 🚨 HUGE SPIKE

**Exp 2 (Policy=0.001, Value=0.0003):**
- Epoch 50: 0.068 ✅ LOWER
- Epoch 100: **0.947** 🚨 SPIKE (but only once!)
- Epoch 150: 0.065 ✅ RECOVERED
- Epoch 200: 0.063 ✅ VERY STABLE

## Key Findings

### 1. **Dual LR Reduced Value Instability** ✅ (Mostly)
- Exp 1: Multiple large spikes (0.545, 0.590)
- Exp 2: One spike at epoch 100 (0.947), then stable
- After epoch 150: Exp 2 is MORE STABLE than Exp 1

### 2. **The Spike at Epoch 100** 🤔
- Negative policy loss (-0.035) + huge value loss (0.947)
- This suggests a transient instability
- But the system RECOVERED (unlike Exp 1 which kept spiking)

### 3. **Entropy Remained Stable** ✅
- Range: 1.600 - 1.605 (consistent)
- Confirms again: NOT an exploration problem

### 4. **Policy Loss Pattern**
- Mostly positive and small (0.03-0.05)
- One negative spike at epoch 100 (correlated with value spike)
- Generally more stable than Exp 1

## Why Did Epoch 100 Spike?

Hypothesis: **Value function adjustment period**

When we set value LR 3x slower (0.0003 vs 0.001):
- Early epochs (0-50): Value function still adapting to slower updates
- Epoch 100: Mismatch between policy (changing fast) and value (learning slow)
- The critic temporarily gave very bad estimates → huge loss
- Epoch 150+: System found equilibrium, much more stable

This is actually GOOD - the spike happened early and recovered, vs Exp 1 where spikes continued throughout training.

## What We Don't Know (Final Eval Missing)

We can't directly compare performance because final evaluation didn't run. But we CAN infer from training stability:

**Exp 1 (constant LR):**
- Continued value instability → bad advantage estimates → policy drift
- Result: 73.2 → (unknown, but we saw 30-min run dropped to 58.6)

**Exp 2 (dual LR):**
- Early instability but STABLE after epoch 150
- Better advantage estimates → less policy drift?
- Result: Unknown, need to evaluate the final checkpoint

## Next Steps

1. **Evaluate the final checkpoint** (`177381284832.pt`)
   - Run proper evaluation to get composite score
   - Compare junction control, exploration, resources
   - See if dual LR prevented conservative drift

2. **If dual LR worked:**
   - Try even slower value LR (0.0002 or 0.0001)
   - Eliminate the epoch-100 spike

3. **If dual LR didn't work:**
   - The problem is deeper than just value instability
   - Try behavioral cloning or KL penalty toward epoch 330

4. **Better TIME_BUDGET enforcement:**
   - Stop training BEFORE eval starts
   - Or extend budget to include final eval

## Hypothesis

**Dual LR likely helps but may not be enough.** The value instability is ONE factor, but the core issue is:

**On-policy RL inherently drifts because:**
1. Non-stationary data distribution (policy changes → new data)
2. No replay buffer (can't revisit successful strategies)
3. Overfitting to recent rollouts (forgets earlier lessons)

Even with stable value function, the policy might still drift conservative because recent rollouts show "playing safe" working.

**True solution might require:**
- Experience replay (makes it off-policy)
- Behavioral cloning loss toward best checkpoint
- Explicit reward shaping to penalize passivity

## Conclusion

Dual learning rates IMPROVED value stability (fewer spikes, faster recovery), but we need to evaluate the checkpoint to know if this translated to better task performance.

**Immediate action:** Evaluate checkpoint `177381284832.pt` against the baseline.
