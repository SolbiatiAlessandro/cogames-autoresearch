#!/usr/bin/env python3
"""Population-Based Training Manager for CoGames.

Runs N agents in sequence, each for a fixed time budget.
After each cycle, bottom 25% copy weights+hyperparams from top 25%.
All agents then perturb hyperparameters ±20% before next cycle.

Usage:
    uv run python pbt/manager.py
"""

import ast
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from prepare import compute_composite_score

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
POP_SIZE = 4              # number of agents (4 = enough selection pressure, fits in memory sequentially)
NUM_CYCLES = 4            # PBT cycles
MINUTES_PER_CYCLE = 5     # minutes each agent trains per cycle
BASE_CHECKPOINT = str(Path(__file__).parent.parent / "best_checkpoint" / "model_000330.pt")
WORK_DIR = Path(__file__).parent.parent / "pbt_run_001"

MISSION = "cogsguard_machina_1.basic"
REWARD_VARIANTS = ["milestones_2:25", "role_conditional", "penalize_vibe_change"]
POLICY_STR = "class=lstm,kw.hidden_size=256"
VECTOR_NUM_ENVS = 64
VECTOR_NUM_WORKERS = 8
MINIBATCH_SIZE = 8192
GAMMA = 0.999
BPTT_HORIZON = 64          # sweet spot from prior experiments

# Hyperparameter search ranges (from PBT_IMPLEMENTATION.md)
LR_RANGE = (0.0003, 0.003)
VALUE_LR_RANGE = (0.0001, 0.001)
ENT_COEF_RANGE = (0.10, 0.25)
GAE_LAMBDA_OPTIONS = [0.90, 0.95, 0.98]


# ---------------------------------------------------------------------------
# Helpers — parse metrics from cogames training output
# ---------------------------------------------------------------------------

def parse_metrics_from_output(output_lines: List[str]):
    """Parse eval/train stats from cogames --log-outputs output."""
    last_eval_stats = {}
    last_train_stats = {}
    context = None
    accumulating = False
    dict_lines = []

    for line in output_lines:
        if "Evaluation:" in line:
            context = "eval"
            continue
        if "Training:" in line:
            context = "train"
            continue
        if "{" in line and context and not accumulating:
            accumulating = True
            dict_lines = [line]
            continue
        elif accumulating:
            dict_lines.append(line)

        if accumulating and "}" in line:
            accumulating = False
            raw = " ".join(dict_lines)
            brace_start = raw.find("{")
            brace_end = raw.rfind("}") + 1
            if brace_start >= 0 and brace_end > brace_start:
                dict_str = raw[brace_start:brace_end]
                dict_str = re.sub(r"np\.float\d+\(([^)]+)\)", r"\1", dict_str)
                dict_str = re.sub(r"\[\d{2}:\d{2}:\d{2}\]", "", dict_str)
                dict_str = re.sub(r"\s+\S+\.py:\d+", "", dict_str)
                try:
                    stats = ast.literal_eval(dict_str)
                    if context == "eval":
                        last_eval_stats = stats
                    elif context == "train":
                        last_train_stats = stats
                except (ValueError, SyntaxError):
                    pass
            dict_lines = []

    return last_eval_stats, last_train_stats


def extract_score_from_log(log_file: Path) -> float:
    """Parse composite_score from training log lines."""
    if not log_file.exists():
        return 0.0

    with open(log_file) as f:
        lines = f.readlines()

    eval_stats, train_stats = parse_metrics_from_output([l.rstrip() for l in lines])

    # Try to extract mean_reward from stats
    mean_reward = 0.0
    reward_prefixes = [
        f"per_label_rewards/{MISSION}",
        f"environment/per_label_rewards/{MISSION}",
        "episode_return",
        "environment/episode_return",
    ]
    for stats in [eval_stats, train_stats]:
        if mean_reward != 0.0:
            break
        for key in stats:
            if any(key == p or key.startswith(p) for p in reward_prefixes):
                val = stats[key]
                if isinstance(val, (list, tuple)):
                    mean_reward = sum(float(v) for v in val) / len(val) if val else 0.0
                else:
                    mean_reward = float(val)
                if mean_reward != 0.0:
                    break

    if mean_reward == 0.0:
        return 0.0

    return compute_composite_score(mean_reward)


def find_latest_checkpoint(checkpoints_dir: Path) -> Optional[Path]:
    """Find the most recently saved checkpoint in a directory."""
    checkpoints = sorted(checkpoints_dir.glob("model_*.pt"))
    if checkpoints:
        return checkpoints[-1]
    return None


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------

class Agent:
    """Single agent in the PBT population."""

    def __init__(self, agent_id: int, base_checkpoint: str, work_dir: Path):
        self.id = agent_id
        self.work_dir = work_dir / f"agent_{agent_id}"
        self.work_dir.mkdir(parents=True, exist_ok=True)

        # Random initial hyperparameters
        rng = np.random.default_rng(seed=agent_id * 42 + 7)
        self.policy_lr = float(rng.uniform(*LR_RANGE))
        self.value_lr = float(rng.uniform(*VALUE_LR_RANGE))
        self.entropy_coef = float(rng.uniform(*ENT_COEF_RANGE))
        self.gae_lambda = float(rng.choice(GAE_LAMBDA_OPTIONS))

        # Copy base checkpoint as starting point
        self.checkpoint = self.work_dir / "current.pt"
        shutil.copy2(base_checkpoint, self.checkpoint)

        # State
        self.score = 0.0
        self.generation = 0

        print(f"  Agent {self.id}: policy_lr={self.policy_lr:.4f} value_lr={self.value_lr:.4f} "
              f"ent={self.entropy_coef:.3f} gae={self.gae_lambda:.2f}")

    def train(self, time_budget: int = 300):
        """Train agent for time_budget seconds."""
        log_file = self.work_dir / f"train_gen{self.generation}.log"
        checkpoints_dir = self.work_dir / f"checkpoints_gen{self.generation}"
        checkpoints_dir.mkdir(parents=True, exist_ok=True)

        checkpoint_path = str(self.checkpoint)
        checkpoints_dir_str = str(checkpoints_dir)

        # Build training script (note: inner braces for dicts must be doubled)
        train_script = f"""
import time
from pathlib import Path
from rich.console import Console
from cogames.cli.mission import get_mission
from cogames.cli.policy import parse_policy_spec
from cogames.cogs_vs_clips.reward_variants import apply_reward_variants
from cogames.device import resolve_training_device
import pufferlib.pufferl as pufferl_module
import cogames.train as train_module

mission = {MISSION!r}
reward_variants = {REWARD_VARIANTS!r}
policy_str = {POLICY_STR!r}

POLICY_LR = {self.policy_lr!r}
VALUE_LR = {self.value_lr!r}
ENT_COEF = {self.entropy_coef!r}
GAE_LAMBDA = {self.gae_lambda!r}
TIME_BUDGET = {time_budget!r}

_OrigPuffeRL = pufferl_module.PuffeRL

class _PatchedPuffeRL(_OrigPuffeRL):
    def __init__(self, train_args, *a, **kw):
        train_args['learning_rate'] = POLICY_LR
        train_args['gamma'] = {GAMMA!r}
        train_args['bptt_horizon'] = {BPTT_HORIZON!r}
        train_args['gae_lambda'] = GAE_LAMBDA
        train_args['ent_coef'] = ENT_COEF
        train_args['clip_coef'] = 0.2
        train_args['vf_coef'] = 0.5
        train_args['update_epochs'] = 1
        super().__init__(train_args, *a, **kw)

        # Dual LR: lower LR for value function to prevent value spikes
        policy_params = []
        value_params = []
        for name, param in self.policy.named_parameters():
            if any(k in name.lower() for k in ('critic', 'value', 'vf')):
                value_params.append(param)
            else:
                policy_params.append(param)
        if policy_params and value_params:
            self.optimizer = type(self.optimizer)([
                {{'params': policy_params, 'lr': POLICY_LR}},
                {{'params': value_params, 'lr': VALUE_LR}},
            ])
        self._start_time = time.time()

    def evaluate(self):
        if time.time() - self._start_time > TIME_BUDGET:
            raise KeyboardInterrupt('PBT time budget reached')
        return super().evaluate()

pufferl_module.PuffeRL = _PatchedPuffeRL

name, env_cfg, _ = get_mission(mission)
apply_reward_variants(env_cfg, variants=reward_variants)
policy_spec = parse_policy_spec(policy_str)
console = Console()
device = resolve_training_device(console, 'auto')

try:
    train_module.train(
        env_cfg=env_cfg,
        policy_class_path=policy_spec.class_path,
        initial_weights_path={checkpoint_path!r},
        device=device,
        num_steps=10_000_000_000,
        checkpoints_path=Path({checkpoints_dir_str!r}),
        seed=42,
        minibatch_size={MINIBATCH_SIZE!r},
        log_outputs=True,
        checkpoint_interval=10,
        vector_num_envs={VECTOR_NUM_ENVS!r},
        vector_num_workers={VECTOR_NUM_WORKERS!r},
    )
except KeyboardInterrupt:
    print('Training complete - time budget reached')
"""

        print(f"  Agent {self.id} gen{self.generation}: training {time_budget}s → {log_file.name}")
        with open(log_file, "w") as log_f:
            proc = subprocess.Popen(
                ["uv", "run", "python", "-c", train_script],
                stdout=log_f,
                stderr=subprocess.STDOUT,
                cwd=str(Path(__file__).parent.parent),
            )
            proc.wait()

        self.generation += 1

        # Update checkpoint to latest saved
        latest_ckpt = find_latest_checkpoint(checkpoints_dir)
        if latest_ckpt:
            shutil.copy2(latest_ckpt, self.checkpoint)
            print(f"  Agent {self.id}: checkpoint updated → {latest_ckpt.name}")
        else:
            print(f"  Agent {self.id}: WARNING — no checkpoint found in {checkpoints_dir}")

    def evaluate(self) -> float:
        log_file = self.work_dir / f"train_gen{self.generation - 1}.log"
        score = extract_score_from_log(log_file)
        self.score = score
        return score

    def copy_from(self, other: "Agent"):
        """Copy weights + hyperparams from a better agent."""
        shutil.copy2(other.checkpoint, self.checkpoint)
        self.policy_lr = other.policy_lr
        self.value_lr = other.value_lr
        self.entropy_coef = other.entropy_coef
        self.gae_lambda = other.gae_lambda
        print(f"  Agent {self.id} ← Agent {other.id} (score {other.score:.2f})")

    def perturb(self, rng=None):
        """Perturb hyperparameters ±20%."""
        if rng is None:
            rng = np.random.default_rng()
        self.policy_lr *= float(rng.uniform(0.8, 1.2))
        self.value_lr *= float(rng.uniform(0.8, 1.2))
        self.entropy_coef *= float(rng.uniform(0.8, 1.2))
        self.policy_lr = float(np.clip(self.policy_lr, 0.0001, 0.01))
        self.value_lr = float(np.clip(self.value_lr, 0.00005, 0.005))
        self.entropy_coef = float(np.clip(self.entropy_coef, 0.05, 0.30))

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "policy_lr": self.policy_lr,
            "value_lr": self.value_lr,
            "entropy_coef": self.entropy_coef,
            "gae_lambda": self.gae_lambda,
            "score": self.score,
            "generation": self.generation,
        }


# ---------------------------------------------------------------------------
# Population
# ---------------------------------------------------------------------------

class PBTPopulation:
    def __init__(self, base_checkpoint: str, pop_size: int, work_dir: Path):
        self.pop_size = pop_size
        self.work_dir = work_dir
        self.work_dir.mkdir(parents=True, exist_ok=True)

        print(f"Initializing {pop_size} agents from {base_checkpoint}")
        self.agents = [Agent(i, base_checkpoint, work_dir) for i in range(pop_size)]
        self._save_population_state(0)

    def train_cycle(self, minutes: int):
        time_budget = minutes * 60
        for agent in self.agents:
            print(f"\n[Cycle] Agent {agent.id}: training {minutes}min...")
            t0 = time.time()
            agent.train(time_budget)
            elapsed = time.time() - t0
            print(f"  Agent {agent.id}: done in {elapsed:.0f}s")

    def evaluate_all(self) -> List[float]:
        scores = []
        for agent in self.agents:
            score = agent.evaluate()
            scores.append(score)
        return scores

    def select_and_replace(self, scores: List[float]):
        n_replace = max(1, self.pop_size // 4)
        sorted_idx = np.argsort(scores)[::-1]
        top_idx = list(sorted_idx[:n_replace])
        bottom_idx = list(sorted_idx[-n_replace:])

        rng = np.random.default_rng()
        for bi in bottom_idx:
            ti = rng.choice(top_idx)
            self.agents[bi].copy_from(self.agents[ti])

    def perturb_all(self):
        rng = np.random.default_rng()
        for agent in self.agents:
            agent.perturb(rng)

    def _save_population_state(self, cycle: int, scores: Optional[List[float]] = None):
        data = {
            "cycle": cycle,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "agents": [a.to_dict() for a in self.agents],
        }
        if scores is not None:
            data["scores"] = scores
        state_file = self.work_dir / f"population_cycle{cycle}.json"
        with open(state_file, "w") as f:
            json.dump(data, f, indent=2)
        print(f"  Saved population state → {state_file.name}")

    def run(self, num_cycles: int, minutes_per_cycle: int):
        print(f"\n{'='*60}")
        print(f"PBT START: {num_cycles} cycles × {minutes_per_cycle}min × {self.pop_size} agents")
        print(f"  Estimated total: ~{num_cycles * minutes_per_cycle * self.pop_size} min sequential")
        print(f"{'='*60}\n")

        for cycle in range(1, num_cycles + 1):
            print(f"\n{'#'*60}")
            print(f"# CYCLE {cycle}/{num_cycles}  [{time.strftime('%H:%M:%S')}]")
            print(f"{'#'*60}")

            for agent in self.agents:
                print(f"  Agent {agent.id}: policy_lr={agent.policy_lr:.4f} "
                      f"value_lr={agent.value_lr:.4f} ent={agent.entropy_coef:.3f}")

            self.train_cycle(minutes=minutes_per_cycle)
            scores = self.evaluate_all()

            print(f"\nCycle {cycle} scores:")
            for i, (agent, score) in enumerate(zip(self.agents, scores)):
                print(f"  Agent {agent.id}: {score:.2f}")
            print(f"  Best={max(scores):.2f}  Mean={np.mean(scores):.2f}  Worst={min(scores):.2f}")

            self._save_population_state(cycle, scores)

            if cycle < num_cycles:
                print("\nSelection + perturbation...")
                self.select_and_replace(scores)
                self.perturb_all()

        # Final summary
        final_scores = [agent.score for agent in self.agents]
        best_idx = int(np.argmax(final_scores))
        best_agent = self.agents[best_idx]

        print(f"\n{'='*60}")
        print("PBT COMPLETE!")
        print(f"  Best agent: Agent {best_idx}, score={final_scores[best_idx]:.2f}")
        print(f"  policy_lr={best_agent.policy_lr:.4f} value_lr={best_agent.value_lr:.4f} "
              f"ent={best_agent.entropy_coef:.3f} gae={best_agent.gae_lambda:.2f}")
        print(f"{'='*60}")

        # Save best checkpoint
        best_out = self.work_dir / "best_agent.pt"
        shutil.copy2(best_agent.checkpoint, best_out)
        print(f"Best checkpoint → {best_out}")

        return best_agent, final_scores


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    assert Path(BASE_CHECKPOINT).exists(), f"Base checkpoint not found: {BASE_CHECKPOINT}"

    pop = PBTPopulation(
        base_checkpoint=BASE_CHECKPOINT,
        pop_size=POP_SIZE,
        work_dir=WORK_DIR,
    )

    best_agent, final_scores = pop.run(
        num_cycles=NUM_CYCLES,
        minutes_per_cycle=MINUTES_PER_CYCLE,
    )

    print("\nFinal scores:", [f"{s:.2f}" for s in final_scores])
    print("Best score:", max(final_scores))
