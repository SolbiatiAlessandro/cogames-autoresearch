"""
CoGames autoresearch training script. Single-file.
This is the ONE file the autoresearch agent modifies.

Usage: uv run train.py

Everything is fair game: policy architecture, hyperparameters, reward
variants, training loop, batch size. The only constraint is that the
code runs without crashing and finishes within the TIME_BUDGET.
"""

import os
import subprocess
import sys
import time

from prepare import TIME_BUDGET, MISSION

# ---------------------------------------------------------------------------
# Configuration — the agent can change ALL of these
# ---------------------------------------------------------------------------

# Mission and reward setup
REWARD_VARIANTS = ["milestones_2"]  # options: objective, milestones, milestones_2, credit, role_conditional
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

# ---------------------------------------------------------------------------
# Training — run cogames tutorial train with the above config
# ---------------------------------------------------------------------------

def build_train_command():
    """Build the cogames training CLI command from config above."""
    cmd = [
        "cogames", "tutorial", "train",
        "-m", MISSION,
        "-p", POLICY,
        "--steps", str(NUM_STEPS),
        "--minibatch-size", str(MINIBATCH_SIZE),
        "--device", DEVICE,
        "--checkpoints", "./train_dir",
    ]

    # Add reward variants
    for variant in REWARD_VARIANTS:
        cmd.extend(["-v", variant])

    return cmd


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
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        # Monitor and enforce time budget
        while True:
            elapsed = time.time() - t_start
            if elapsed > TIME_BUDGET:
                print(f"\n[TIME BUDGET] {TIME_BUDGET}s exceeded, stopping training...")
                process.terminate()
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    process.kill()
                break

            # Read output line by line
            if process.poll() is not None:
                break
            # TODO: stream output more cleanly
            time.sleep(1)

        returncode = process.returncode or 0

    except FileNotFoundError:
        print("ERROR: 'cogames' CLI not found. Install with: pip install cogames")
        sys.exit(1)

    training_seconds = time.time() - t_start

    # ---------------------------------------------------------------------------
    # Evaluation
    # ---------------------------------------------------------------------------

    print("\n" + "=" * 60)
    print("Evaluation")
    print("=" * 60)

    # TODO: Find the latest checkpoint in train_dir/ and evaluate it
    # For now, run cogames eval on the checkpoint
    #
    # checkpoint = find_latest_checkpoint("./train_dir")
    # results = evaluate(checkpoint)
    #
    # Placeholder metrics:
    composite_score = 0.0
    mean_reward = 0.0
    explained_var = 0.0

    # TODO: Extract real metrics from training output and evaluation
    # Look for PufferLib dashboard output, extract:
    # - mean_reward from eval stats
    # - explained_variance from trainer stats
    # - entropy from trainer stats

    # ---------------------------------------------------------------------------
    # Output format (matches autoresearch pattern)
    # ---------------------------------------------------------------------------

    # TODO: Get actual VRAM usage
    try:
        import torch
        if torch.cuda.is_available():
            peak_vram_mb = torch.cuda.max_memory_allocated() / 1024 / 1024
        else:
            peak_vram_mb = 0.0
    except ImportError:
        peak_vram_mb = 0.0

    print("\n---")
    print(f"composite_score:  {composite_score:.6f}")
    print(f"mean_reward:      {mean_reward:.6f}")
    print(f"explained_var:    {explained_var:.6f}")
    print(f"training_seconds: {training_seconds:.1f}")
    print(f"peak_vram_mb:     {peak_vram_mb:.1f}")
    print(f"mission:          {MISSION}")
    print(f"policy:           {POLICY}")
    print(f"reward_variants:  {','.join(REWARD_VARIANTS)}")


if __name__ == "__main__":
    main()
