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
REWARD_VARIANTS = ["milestones_2"]  # available: standard, hard, speed_run, etc. (see `cogames variants`)
NUM_AGENTS = 4

# Policy
POLICY = "class=lstm"  # options: lstm, baseline, stateless, or custom class path
HIDDEN_SIZE = 256

# Training hyperparameters
LEARNING_RATE = 0.00092
MINIBATCH_SIZE = 4096
NUM_STEPS = 10_000_000_000  # effectively infinite — TIME_BUDGET is the real limit

# Hardware
DEVICE = "auto"  # auto, cpu, cuda, mps

# Experiment description (for results.tsv logging)
DESCRIPTION = "milestones_2 baseline"

# ---------------------------------------------------------------------------
# Training — run cogames tutorial train with the above config
# ---------------------------------------------------------------------------


def build_train_command():
    """Build the cogames training CLI command from config above."""
    cmd = [
        "cogames",
        "tutorial",
        "train",
        "-m",
        MISSION,
        "-p",
        POLICY,
        "--steps",
        str(NUM_STEPS),
        "--minibatch-size",
        str(MINIBATCH_SIZE),
        "--device",
        DEVICE,
        "--checkpoints",
        "./train_dir",
        "--log-outputs",
    ]

    # Add reward variants
    for variant in REWARD_VARIANTS:
        cmd.extend(["-v", variant])

    return cmd


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
    commit, composite_score, mean_reward, memory_gb, status, description
):
    """Append a row to results.tsv, creating the file with header if needed."""
    tsv_path = "results.tsv"
    write_header = not os.path.exists(tsv_path)

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
                ]
            )
        writer.writerow(
            [
                commit,
                f"{composite_score:.6f}",
                f"{mean_reward:.6f}",
                f"{memory_gb:.3f}",
                status,
                description,
            ]
        )


def main():
    t_start = time.time()

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
    print(f"\nRunning: {' '.join(cmd)}\n")

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
        print("ERROR: 'cogames' CLI not found. Install with: pip install cogames")
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
    # Eval stats use keys like 'per_label_rewards/cogsguard_machina_1.basic'
    # Train stats use keys like 'environment/per_label_rewards/...'
    mean_reward = 0.0
    reward_keys = [
        f"per_label_rewards/{MISSION}",
        f"environment/per_label_rewards/{MISSION}",
        "episode_return",
        "environment/episode_return",
    ]
    # Check eval stats first, then train stats
    for stats in [eval_stats, train_stats]:
        if mean_reward != 0.0:
            break
        for key in reward_keys:
            if key in stats:
                val = stats[key]
                if isinstance(val, (list, tuple)):
                    mean_reward = sum(val) / len(val) if val else 0.0
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

    # Composite score (deposit_diversity=0 for now, just mean_reward)
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

    # ---------------------------------------------------------------------------
    # Log to results.tsv
    # ---------------------------------------------------------------------------

    commit = get_commit_hash()
    memory_gb = peak_vram_mb / 1024.0
    status = "keep" if composite_score > 0 else "crash" if returncode != 0 else "keep"

    log_to_results_tsv(
        commit, composite_score, mean_reward, memory_gb, status, DESCRIPTION
    )
    print(
        f"\nLogged to results.tsv: {commit} | {composite_score:.6f} | {status} | {DESCRIPTION}"
    )


if __name__ == "__main__":
    main()
