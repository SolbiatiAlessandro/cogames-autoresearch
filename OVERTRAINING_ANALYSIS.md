# Overtraining Analysis - March 18, 2026

## Experiment Setup

Compared two fresh training runs with identical hyperparameters:
- **10-min run:** Stopped at epoch 337 → **score 73.2** ✅
- **30-min run:** Continued to epoch 885 → **score 58.6** ↘️ (20% worse)

Config: milestones_2:25 + role_conditional + penalize_vibe_change, lr=0.001, ent=0.15, gamma=0.999

## Key Findings

### 1. Performance degrades with continued training
- Score drops from 73.2 to 58.6 when training 3x longer
- Checkpoint at epoch 330 (~11 min) likely has similar performance to epoch 337
- Training beyond this point hurts performance

### 2. NOT an exploration collapse
- Entropy remained stable throughout training (~1.59)
- No catastrophic drop in policy diversity
- Agent maintains behavioral variety

### 3. NOT a checkpoint loading bug
- Earlier hypothesis (checkpoint resumption causing degradation) was wrong
- Degradation happens even in single continuous fresh runs
- The 10-min segmented runs coincidentally stopped near the optimal point

### 4. Root cause: On-policy training instability
MAPPO trains on fresh rollouts each epoch. After ~337 epochs:
- Policy has learned effective behaviors
- Continued training on new rollouts causes **policy drift**
- Agent "forgets" earlier successful strategies
- Overfits to recent experiences (catastrophic forgetting)

## Why This Happens in MAPPO

On-policy RL algorithms like MAPPO:
- Only learn from recent trajectories (no replay buffer)
- Each update shifts the policy → changes the data distribution → next update sees different data
- This creates a **non-stationary learning problem**
- Eventually the policy drifts away from the behaviors that worked early on

## Solutions

### Immediate (quick wins):
1. **Use 10-minute training** (already working!) - epoch ~300-350 is the sweet spot
2. **Save checkpoints every 50-100 epochs** and evaluate to find the peak
3. **Learning rate decay** - reduce LR after epoch 200 to stabilize policy

### Medium-term (improve robustness):
4. **Validation-based early stopping** - evaluate every N epochs, stop when score plateaus
5. **Learning rate schedule** - use cosine decay or reduce LR when score drops
6. **Gradient clipping tuning** - might help with policy drift

### Long-term (architectural changes):
7. **Add experience replay** (but this makes it off-policy)
8. **PPO → SAC/TD3** - off-policy methods more stable for long training
9. **Ensemble checkpoints** - average policy across last N checkpoints

## Recommendation

**Stick with 10-minute training runs** for now. This is the sweet spot where:
- Policy has learned good behaviors
- Hasn't started drifting yet
- Training time is practical for iteration

If we want longer training, implement solution #4 (validation-based early stopping) to automatically detect the optimal point.

## Next Steps

1. ✅ Document these findings
2. Run 3-5 more 10-min experiments to confirm 73.2 is reproducible
3. Try learning rate decay (e.g., multiply LR by 0.5 at epoch 200)
4. Implement checkpoint evaluation script to find best epoch automatically

---
**Conclusion:** The "checkpoint resumption bug" was actually "optimal stopping time discovery". Training for 10 minutes hits a natural peak before policy drift sets in.
