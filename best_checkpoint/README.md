# Best Checkpoint - Score 73.2

**Run:** march-17-best-MAPPO-baseline, first fresh run (03:01 UTC, Mar 18 2026)

**Results:**
- Composite score: 73.208916
- Cogs junctions held: 0.0
- Clips junctions held: 1,197,292.5
- Aligned by agent: 0.0
- Heart amount: 1.6

**Config:**
- Reward variants: milestones_2:25 + role_conditional + penalize_vibe_change
- Hyperparams: ent=0.15, lr=0.001, gamma=0.999, gae=0.95
- Training time: 10 minutes (TIME_BUDGET=600)
- Architecture: LSTM, hidden_size=256
- Epochs: ~337

**Note:** This was a fresh-start run (no checkpoint loading). Subsequent runs with checkpoint resumption showed performance degradation (43-57 range).

## Files
Checkpoint files are packaged in `best_checkpoint_score_73.2.tar.gz` (33 model checkpoints + trainer state).
