"""
CoGames autoresearch training script. Single-file.
This is the ONE file the autoresearch agent modifies.

Usage: uv run train.py

Everything is fair game: policy architecture, hyperparameters, reward
variants, training loop, batch size. The only constraint is that the
code runs without crashing and finishes within the TIME_BUDGET.
"""

import ast
import csv
import glob
import os
import re
import subprocess
import sys
import time

from prepare import TIME_BUDGET, MISSION, compute_composite_score

# ---------------------------------------------------------------------------
# Configuration — the agent can change ALL of these
# ---------------------------------------------------------------------------

# Mission and reward setup
REWARD_VARIANTS = ["milestones_2", "role_conditional", "penalize_vibe_change", "credit", "scout"]  # available: objective, milestones, milestones_2, milestones_2:N, credit, miner, aligner, scrambler, scout, role_conditional, penalize_vibe_change
NUM_AGENTS = 4

# Policy
POLICY = "class=lstm"  # options: lstm, baseline, stateless, or custom class path
HIDDEN_SIZE = 256

# Training hyperparameters
LEARNING_RATE = 0.002  # 2x default; dense credit+scout rewards may allow faster convergence
MINIBATCH_SIZE = 8192
GAMMA = 0.995  # default
BPTT_HORIZON = 64  # default
NUM_STEPS = 10_000_000_000  # effectively infinite — TIME_BUDGET is the real limit

# Hardware
DEVICE = "auto"  # auto, cpu, cuda, mps

# Experiment description (for results.tsv logging)
DESCRIPTION = "milestones_2 + role_conditional + penalize_vibe_change + credit + scout lr=0.002"

# ---------------------------------------------------------------------------
# Training — use cogames Python API directly to support reward variants
# ---------------------------------------------------------------------------

TRAIN_SCRIPT = """
import sys
from pathlib import Path
from rich.console import Console
from cogames.cli.mission import get_mission
from cogames.cli.policy import parse_policy_spec
from cogames.cogs_vs_clips.reward_variants import apply_reward_variants
from cogames.device import resolve_training_device
import pufferlib.pufferl as pufferl_module
import cogames.train as train_module

mission = {mission!r}
reward_variants = {reward_variants!r}
policy_str = {policy!r}
device_str = {device!r}
num_steps = {num_steps!r}
minibatch_size = {minibatch_size!r}
checkpoints = {checkpoints!r}
learning_rate = {learning_rate!r}
gamma = {gamma!r}
bptt_horizon = {bptt_horizon!r}

_OrigPuffeRL = pufferl_module.PuffeRL
class _PatchedPuffeRL(_OrigPuffeRL):
    def __init__(self, train_args, *args, **kwargs):
        train_args['learning_rate'] = learning_rate
        train_args['gamma'] = gamma
        train_args['bptt_horizon'] = bptt_horizon
        super().__init__(train_args, *args, **kwargs)
pufferl_module.PuffeRL = _PatchedPuffeRL

name, env_cfg, _ = get_mission(mission)
if reward_variants:
    apply_reward_variants(env_cfg, variants=reward_variants)

policy_spec = parse_policy_spec(policy_str)
console = Console()
device = resolve_training_device(console, device_str)

train_module.train(
    env_cfg=env_cfg,
    policy_class_path=policy_spec.class_path,
    initial_weights_path=policy_spec.data_path,
    device=device,
    num_steps=num_steps,
    checkpoints_path=Path(checkpoints),
    seed=42,
    minibatch_size=minibatch_size,
    log_outputs=True,
    checkpoint_interval=10,
)
"""


def build_train_command():
    """Build the training command using cogames Python API (supports reward variants)."""
    script = TRAIN_SCRIPT.format(
        mission=MISSION,
        reward_variants=REWARD_VARIANTS,
        policy=POLICY,
        device=DEVICE,
        num_steps=NUM_STEPS,
        minibatch_size=MINIBATCH_SIZE,
        checkpoints="./train_dir",
        learning_rate=LEARNING_RATE,
        gamma=GAMMA,
        bptt_horizon=BPTT_HORIZON,
    )
    return ["uv", "run", "python", "-c", script]


def find_latest_checkpoint(train_dir="./train_dir"):
    """Find the most recent model checkpoint in train_dir."""
    pattern = os.path.join(train_dir, "**", "model_*.pt")
    checkpoints = glob.glob(pattern, recursive=True)
    if not checkpoints:
        return None
    return max(checkpoints, key=os.path.getmtime)


def parse_metrics_from_output(output_lines):
    """Parse mean_reward and explained_variance from cogames --log-outputs output.

    The --log-outputs flag streams eval and training stats as Rich-formatted dicts
    spread across multiple lines, with numpy wrappers like np.float64(...).

    We accumulate lines between { and }, strip numpy wrappers, and parse as Python dicts.
    """
    last_eval_stats = {}
    last_train_stats = {}

    context = None  # "eval" or "train"
    accumulating = False
    dict_lines = []

    for line in output_lines:
        if "Evaluation:" in line:
            context = "eval"
            continue
        if "Training:" in line:
            context = "train"
            continue

        # Start accumulating when we see an opening brace
        if "{" in line and context and not accumulating:
            accumulating = True
            dict_lines = [line]
            continue
        elif accumulating:
            dict_lines.append(line)

        # Check if we've closed the dict
        if accumulating and "}" in line:
            accumulating = False
            raw = " ".join(dict_lines)

            # Extract the dict substring
            brace_start = raw.find("{")
            brace_end = raw.rfind("}") + 1
            if brace_start >= 0 and brace_end > brace_start:
                dict_str = raw[brace_start:brace_end]
                # Strip numpy wrappers: np.float64(x) -> x, np.float32(x) -> x
                dict_str = re.sub(r"np\.float\d+\(([^)]+)\)", r"\1", dict_str)
                # Strip Rich markup tags like [HH:MM:SS]
                dict_str = re.sub(r"\[\d{2}:\d{2}:\d{2}\]", "", dict_str)
                # Strip Rich file references like train.py:332
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


def get_commit_hash():
    """Get short git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short=7", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def log_to_results_tsv(
    commit, composite_score, mean_reward, memory_gb, status, description,
    game_metrics=None, e2e_seconds=0.0, api_cost_usd=0.0,
):
    """Append a row to results.tsv, creating the file with header if needed."""
    tsv_path = "results.tsv"
    write_header = not os.path.exists(tsv_path)
    if game_metrics is None:
        game_metrics = {}

    with open(tsv_path, "a", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        if write_header:
            writer.writerow(
                [
                    "commit",
                    "composite_score",
                    "mean_reward",
                    "memory_gb",
                    "status",
                    "description",
                    "e2e_seconds",
                    "api_cost_usd",
                ]
                + list(game_metrics.keys())
            )
        writer.writerow(
            [
                commit,
                f"{composite_score:.6f}",
                f"{mean_reward:.6f}",
                f"{memory_gb:.3f}",
                status,
                description,
                f"{e2e_seconds:.0f}",
                f"{api_cost_usd:.4f}",
            ]
            + [f"{v:.1f}" for v in game_metrics.values()]
        )


def main():
    t_start = time.time()

    experiment_start_time = time.time()

    print("=" * 60)
    print("CoGames Autoresearch Training")
    print("=" * 60)
    print(f"Mission:          {MISSION}")
    print(f"Policy:           {POLICY}")
    print(f"Reward variants:  {REWARD_VARIANTS}")
    print(f"Learning rate:    {LEARNING_RATE}")
    print(f"Minibatch size:   {MINIBATCH_SIZE}")
    print(f"Time budget:      {TIME_BUDGET}s")
    print(f"Device:           {DEVICE}")
    print("=" * 60)

    cmd = build_train_command()
    print(f"\nRunning: uv run python -c <train_script> (mission={MISSION}, variants={REWARD_VARIANTS})\n")

    # Run training with time budget enforcement
    output_lines = []
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # line-buffered
        )

        # Stream output line by line, enforce time budget
        for line in iter(process.stdout.readline, ""):
            line = line.rstrip("\n")
            output_lines.append(line)
            print(line, flush=True)

            elapsed = time.time() - t_start
            if elapsed > TIME_BUDGET:
                print(f"\n[TIME BUDGET] {TIME_BUDGET}s exceeded, stopping training...")
                process.terminate()
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    process.kill()
                break

        process.wait()
        returncode = process.returncode or 0

    except FileNotFoundError:
        print("ERROR: 'uv' not found.")
        sys.exit(1)

    training_seconds = time.time() - t_start

    # ---------------------------------------------------------------------------
    # Extract metrics from training output
    # ---------------------------------------------------------------------------

    print("\n" + "=" * 60)
    print("Results")
    print("=" * 60)

    eval_stats, train_stats = parse_metrics_from_output(output_lines)

    # Extract mean_reward from stats
    # The label key may have variant names appended: e.g. "MISSION.milestones_2"
    mean_reward = 0.0
    reward_prefixes = [
        f"per_label_rewards/{MISSION}",
        f"environment/per_label_rewards/{MISSION}",
        "episode_return",
        "environment/episode_return",
    ]
    # Check eval stats first, then train stats; use prefix match for label keys
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

    # Extract explained_variance from training stats
    explained_var = 0.0
    for key in ["losses/explained_variance", "explained_variance"]:
        if key in train_stats:
            explained_var = float(train_stats[key])
            break

    # ---------------------------------------------------------------------------
    # Game metrics (track actual game performance, not just shaped rewards)
    # ---------------------------------------------------------------------------
    # All game metrics we want to track — give the researcher full visibility
    GAME_METRIC_KEYS = {
        # === OBJECTIVE (the actual game goal) ===
        "cogs_junctions_held":       ["game/cogs/aligned.junction.held"],
        "cogs_junctions_aligned":    ["game/cogs/aligned.junction"],
        "clips_junctions_held":      ["game/clips/aligned.junction.held"],
        # === AGENT ACTIONS (are agents doing useful things?) ===
        "aligned_by_agent":          ["agent/junction.aligned_by_agent"],
        "scrambled_by_agent":        ["agent/junction.scrambled_by_agent"],
        "cells_visited":             ["agent/cell.visited"],
        "deaths":                    ["agent/death"],
        "move_success":              ["agent/action.move.success"],
        "move_failed":               ["agent/action.move.failed"],
        "vibe_changes":              ["agent/action.change_vibe.success"],
        # === ECONOMY (resource flow) ===
        "carbon_deposited":          ["game/cogs/carbon.deposited"],
        "carbon_amount":             ["game/cogs/carbon.amount"],
        "oxygen_amount":             ["game/cogs/oxygen.amount"],
        "silicon_amount":            ["game/cogs/silicon.amount"],
        "germanium_amount":          ["game/cogs/germanium.amount"],
        "heart_amount":              ["game/cogs/heart.amount"],
        # === GEAR (specialization happening?) ===
        "miner_gained":              ["agent/miner.gained"],
        "aligner_gained":            ["agent/aligner.gained"],
        "scrambler_gained":          ["agent/scrambler.gained"],
        "scout_gained":              ["agent/scout.gained"],
    }
    game_metrics = {k: 0.0 for k in GAME_METRIC_KEYS}
    for metric_name, keys in GAME_METRIC_KEYS.items():
        for stats in [eval_stats, train_stats]:
            for key in keys:
                # Also check with environment/ prefix
                for full_key in [key, f"environment/{key}"]:
                    if full_key in stats:
                        val = stats[full_key]
                        if isinstance(val, (list, tuple)):
                            game_metrics[metric_name] = sum(float(v) for v in val) / len(val) if val else 0.0
                        else:
                            game_metrics[metric_name] = float(val)
                        break
                if game_metrics[metric_name] != 0.0:
                    break
            if game_metrics[metric_name] != 0.0:
                break

    # Composite score
    composite_score = compute_composite_score(mean_reward)

    # Find checkpoint
    checkpoint = find_latest_checkpoint()
    if checkpoint:
        print(f"Checkpoint:       {checkpoint}")
    else:
        print("Checkpoint:       (none found)")

    # VRAM usage
    try:
        import torch

        if torch.cuda.is_available():
            peak_vram_mb = torch.cuda.max_memory_allocated() / 1024 / 1024
        else:
            peak_vram_mb = 0.0
    except ImportError:
        peak_vram_mb = 0.0

    # ---------------------------------------------------------------------------
    # Output format (matches autoresearch pattern)
    # ---------------------------------------------------------------------------

    print("\n---")
    print(f"composite_score:  {composite_score:.6f}")
    print(f"mean_reward:      {mean_reward:.6f}")
    print(f"explained_var:    {explained_var:.6f}")
    print(f"training_seconds: {training_seconds:.1f}")
    print(f"peak_vram_mb:     {peak_vram_mb:.1f}")
    print(f"mission:          {MISSION}")
    print(f"policy:           {POLICY}")
    print(f"reward_variants:  {','.join(REWARD_VARIANTS)}")
    print("\n--- Game Metrics ---")
    for k, v in game_metrics.items():
        print(f"{k:>25}: {v:.1f}")

    # ---------------------------------------------------------------------------
    # Log to results.tsv
    # ---------------------------------------------------------------------------

    commit = get_commit_hash()
    memory_gb = peak_vram_mb / 1024.0
    status = "keep" if composite_score > 0 else "crash" if returncode != 0 else "keep"
    e2e_seconds = time.time() - experiment_start_time

    # Estimate API cost from a cost file written by the loop (if available)
    api_cost_usd = 0.0
    cost_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".experiment_cost")
    if os.path.exists(cost_file):
        try:
            api_cost_usd = float(open(cost_file).read().strip())
            os.remove(cost_file)
        except Exception:
            pass

    print(f"e2e_seconds:      {e2e_seconds:.1f}")
    print(f"api_cost_usd:     ${api_cost_usd:.4f}")

    log_to_results_tsv(
        commit, composite_score, mean_reward, memory_gb, status, DESCRIPTION,
        game_metrics=game_metrics,
        e2e_seconds=e2e_seconds,
        api_cost_usd=api_cost_usd,
    )
    print(
        f"\nLogged to results.tsv: {commit} | {composite_score:.6f} | {status} | {DESCRIPTION}"
    )


if __name__ == "__main__":
    main()
