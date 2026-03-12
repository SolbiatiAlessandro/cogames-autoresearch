# Memory Issues & Env Scaling

## The Problem

On machines with many CPU cores, `cogames.train.train()` auto-detects physical core count and uses it for `num_workers`, then adjusts `num_envs` to be divisible. On a 96-core machine this means **48 workers × 288 envs**. This causes training to hang or OOM during initialization — before a single training step runs. The symptom is `run.log` ending abruptly after the Pydantic serializer warnings with no Python traceback.

The same issue happened on Mac in a different form: Serial backend (1 worker) but 256 env instances all in the main process, which is heavy on low-RAM machines.

## The Fix

Always pass explicit `vector_num_envs` and `vector_num_workers` to `train_module.train()`. These are already wired into `train.py`:

```python
VECTOR_NUM_ENVS = 64    # sane default; was auto-scaling to 288
VECTOR_NUM_WORKERS = 8  # sane default; was using all 48 physical cores
```

Do **not** remove these or set them to `None` — the auto-detection will break training.

## Between-Experiment Memory

Each experiment runs `train_module.train()` inside a subprocess (`uv run python -c <script>`). When the subprocess exits, all RAM and VRAM is released automatically. No explicit `torch.cuda.empty_cache()` or `gc.collect()` is needed between experiments.

## BPTT and Batch Size

`BPTT_HORIZON` directly controls the experience buffer size: `batch_size = total_agents × bptt_horizon`. With 64 envs × 8 agents = 512 agents:

| BPTT | batch_size | obs buffer (GPU) |
|------|-----------|-----------------|
| 64   | 32,768    | ~20 MB          |
| 128  | 65,536    | ~40 MB          |
| 256  | 131,072   | ~79 MB          |

All fit easily in a 46 GB A40. But very high BPTT values slow down the update cycle (fewer PPO updates per second). Keep BPTT ≤ 256 unless you have a specific reason.

## Environment Facts

- Mission `cogsguard_machina_1.basic`: obs space **(200, 3) uint8**, **8 agents per env**
- 64 envs × 8 agents = **512 total agents** (manageable on any hardware)
- Worker processes each load Python + torch + cogames (~500 MB each); keep `VECTOR_NUM_WORKERS` ≤ 16
