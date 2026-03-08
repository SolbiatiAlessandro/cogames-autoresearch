# PufferLib Training Tips for CoGames

## Current Default Hyperparameters (from cogames/train.py)

| Parameter         | Value   | Notes                              |
|-------------------|---------|------------------------------------|
| learning_rate     | 0.00092 | Annealed to 0 over training        |
| gamma             | 0.995   | Discount factor (high = long-horizon) |
| gae_lambda        | 0.90    | GAE parameter                      |
| clip_coef         | 0.2     | PPO clipping                       |
| vf_coef           | 2.0     | Value function loss weight          |
| vf_clip_coef      | 0.2     | Value function clipping             |
| ent_coef          | 0.01    | Entropy bonus (exploration)         |
| max_grad_norm     | 1.5     | Gradient clipping                   |
| update_epochs     | 1       | PPO epochs per batch                |
| bptt_horizon      | 64      | LSTM backprop-through-time horizon  |
| adam_beta1         | 0.95    | Adam optimizer                      |
| adam_beta2         | 0.999   | Adam optimizer                      |
| adam_eps           | 1e-8    | Adam optimizer                      |
| precision          | float32 | Training precision                  |

## What to Try

### High-impact knobs
1. **Reward variants** — milestones_2 compounding factor (try 1, 5, 10, 25, 50)
2. **Entropy coefficient** — 0.01 is low; try 0.05-0.1 for more exploration
3. **Learning rate** — try 0.001, 0.0005, 0.002
4. **Network size** — hidden_size 128, 256, 512

### Medium-impact
5. **GAE lambda** — 0.90 vs 0.95 vs 0.99
6. **Gamma** — 0.995 vs 0.99 vs 0.999
7. **Update epochs** — 1 vs 3 vs 5
8. **Minibatch size** — 2048, 4096, 8192

### Architecture experiments
9. **With/without LSTM** — stateless vs lstm policy
10. **Hidden size scaling** — 128 → 256 → 512
11. **Separate critic** — shared vs separate value network

## Common Failure Modes
- **Policy collapse**: entropy drops to near 0, all agents do the same thing.
  Fix: increase ent_coef, add entropy floor.
- **Value function explosion**: vf_loss grows unbounded.
  Fix: reduce learning rate, increase vf_clip_coef.
- **NaN gradients**: training diverges.
  Fix: reduce learning rate, increase max_grad_norm.
- **No role specialization**: all agents pick the same role.
  Fix: try role_conditional rewards or milestones_2 with higher compounding.
- **Agents ignore each other**: no coordination behaviors emerge.
  Fix: this is THE research problem. See social influence papers in knowledge/.
