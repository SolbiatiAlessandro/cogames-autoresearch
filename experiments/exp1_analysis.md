# Experiment 1 Analysis - Continue Training from Best Checkpoint

## Setup
- **Base:** Checkpoint epoch 330 (score ~73.2 from 10-min fresh run)
- **Training:** Continued for 68 more epochs (epoch 330 → 398)
- **Runtime:** 26+ minutes
- **Config:** LR=0.001 (constant, decay didn't trigger), ent=0.15
- **Note:** Accidentally trained longer than intended (no TIME_BUDGET enforcement)

## Training Metrics Progression

| Epoch | Policy Loss | Value Loss | Entropy | Notes |
|-------|-------------|------------|---------|-------|
| 10    | 0.035       | 0.039      | 1.600   | Early, stable |
| 50    | 0.066       | 0.187      | 1.597   | Value loss rising |
| 100   | 0.059       | 0.099      | 1.587   | Stabilizing |
| 150   | 0.102       | 0.545      | 1.583   | **Value loss spike** |
| 200   | 0.071       | 0.157      | 1.591   | Recovering |
| 250   | 0.057       | 0.148      | 1.605   | Stable |
| 300   | 0.037       | 0.062      | 1.602   | **Best losses** |
| 350   | **-0.047**  | 0.590      | 1.602   | **Negative policy loss!** |
| 398   | 0.045       | 0.115      | 1.604   | End |

## Key Observations

### 1. **Entropy Stayed Stable** ✅
- Range: 1.583 - 1.605 (very consistent)
- No exploration collapse
- Confirms our earlier finding: entropy is NOT the problem

### 2. **Value Loss Instability** ⚠️
- Large spikes at epochs 50, 150, 350
- Value function struggling to track policy changes
- Suggests the critic can't keep up with policy updates

### 3. **Negative Policy Loss at Epoch 350** 🚨
- This is unusual and concerning
- Indicates potential training instability
- Policy gradient flipped sign (optimizer confusion?)

### 4. **Losses Improving at Epoch 300** 📈
- Policy loss: 0.037 (lowest yet)
- Value loss: 0.062 (very low)
- This was ~20 minutes in
- **Hypothesis:** Model might have peaked here

## What This Tells Us

**The problem is NOT:**
- ❌ Exploration collapse (entropy stable)
- ❌ Learning rate too high (losses generally decreasing)

**The problem IS:**
- ✅ **Value function instability** - critic can't track the changing policy
- ✅ **Policy drift** - even with good losses, behavior degrades (we saw 73.2 → 58.6)
- ✅ **Lack of stopping criterion** - no way to know when to stop

## Why Performance Degrades Despite Good Losses

Training losses measure "how well does the update fit recent rollouts."
Performance measures "how well does the policy solve the task."

These can diverge when:
1. **Non-stationary data** - each policy change creates new data distribution
2. **Overfitting to recent rollouts** - policy fits latest batch but forgets earlier strategies
3. **Value function lag** - critic gives bad advantage estimates → bad policy updates

## Recommendations

### Immediate fixes:
1. **Early stopping based on validation** - evaluate every N epochs, stop when perf drops
2. **Checkpoint every 50 epochs** - keep best performing checkpoint
3. **VALUE FUNCTION: lower learning rate** - critic updates too fast, use separate LR
4. **Gradient clipping** - prevent large policy updates that destabilize value function

### Better solutions:
5. **PPO with value function warmup** - train critic first before policy updates
6. **Dual learning rates** - policy: 0.001, value: 0.0003
7. **Trust region constraint** - harder KL penalty to prevent policy drift
8. **Experience replay** (requires off-policy) - maintain replay buffer to avoid forgetting

## Next Experiment Ideas

1. **Separate LR for value function** (policy: 0.001, value: 0.0003)
2. **Harder KL constraint** (increase clip_coef or add KL penalty)
3. **Checkpoint evaluation** - eval epochs 100, 200, 300 to find peak
4. **VF warmup** - train value function 5 epochs before each policy update

My vote: **Try #1 (separate value LR)** - this directly addresses the value instability we see.
