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
from datetime import datetime

from prepare import TIME_BUDGET as _DEFAULT_TIME_BUDGET, MISSION as _DEFAULT_MISSION, compute_composite_score
MISSION = "cogsguard_machina_1.basic"  # best known map (arena failed: 83.4j vs machina 552.6j)
TIME_BUDGET = 540  # 9min — testing BPTT=256 at 10min: BPTT=128→1029j, BPTT=64→87j; does BPTT=256 beat 128?

# ---------------------------------------------------------------------------
# Configuration — the agent can change ALL of these
# ---------------------------------------------------------------------------

# Mission and reward setup
REWARD_VARIANTS = ["milestones_2:25", "role_conditional", "penalize_vibe_change"]  # BEST KNOWN: milestones_2:25 + role_conditional + penalize_vibe_change → 552.6j at 20min, 1029j at 10min
NUM_AGENTS = 4

# Policy
HIDDEN_SIZE = 256
POLICY = f"class=lstm,kw.hidden_size={HIDDEN_SIZE}"  # LSTM — best architecture

# Training hyperparameters
# Best 20min config: ent=0.10, single LR=0.001, BPTT=64, gae=0.95, minibatch=8192 → 552.6 junctions (ae6f8d2)
# This experiment: milestones_2:50 (higher milestone weight, :25 was best at 552.6j, testing if :50 helps)
LEARNING_RATE = 0.001    # constant LR (no warmup — warmup failed badly: 99.4j)
LR_WARMUP_START = 0.001  # no warmup: same as target LR
LR_WARMUP_DURATION = 0   # disabled
VALUE_LR = 0.001         # same as policy LR
MINIBATCH_SIZE = 8192  # best known minibatch (16384 failed 27j, 4096 failed 54j)
GAMMA = 0.999  # best gamma (0.999 → 552.6j; 0.99 → 124.1j FAIL)
GAE_LAMBDA = 0.95  # best GAE from prior sessions (gae=0.98 tested → 447j, 0.95 best=552j)
BPTT_HORIZON = 256  # NEW: testing BPTT=256 at 10min — BPTT=128→1029j, BPTT=64→87j at 10min; longer context hypothesis
ENT_COEF_START = 0.15  # best 10min entropy (0.15 + BPTT=128 → 1029j at 10min; ent=0.10 optimal at 20min)
ENT_COEF_END = 0.15    # constant entropy (no annealing — all annealing variants fail)
ENT_COEF = ENT_COEF_START  # placeholder for logging
VECTOR_BATCH_SIZE = 128  # default rollout (256 tested → 99.4j, 82% drop!)
LR_DROP_TIME = 9999    # disabled (step LR failed: 190j; constant LR best)
LR_FINAL = 0.001       # same as base (no step LR)
NUM_STEPS = 10_000_000_000  # effectively infinite — TIME_BUDGET is the real limit

# Hardware
DEVICE = "auto"  # auto, cpu, cuda, mps
VECTOR_NUM_ENVS = 64   # cap env count (safe default)
VECTOR_NUM_WORKERS = 8  # cap worker processes (default uses all physical cores = 48 here)

# Experiment description (for results.tsv logging)
DESCRIPTION = "milestones_2:25 + role_conditional + penalize_vibe_change LSTM ent=0.15 bptt=256 gae=0.95 lr=0.001 minibatch=8192 machina 9min — NOVEL: BPTT=256 at 10min extending BPTT upward; best 10min BPTT=128(1029j,96b72bf), BPTT=64 failed at 10min(87j); trend: smaller BPTT=worse at 10min; hypothesis BPTT=256 doubles context=more gradient signal per step=faster learning; using best 10min params (ent=0.15, lr=0.001)"

# ---------------------------------------------------------------------------
# Training — use cogames Python API directly to support reward variants
# ---------------------------------------------------------------------------

TRAIN_SCRIPT = """
import sys
import time as _time_module
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
lr_warmup_start = {lr_warmup_start!r}
lr_warmup_duration = {lr_warmup_duration!r}
value_lr = {value_lr!r}
gamma = {gamma!r}
bptt_horizon = {bptt_horizon!r}
gae_lambda = {gae_lambda!r}
ent_start = {ent_start!r}
ent_end = {ent_end!r}
anneal_duration = {time_budget!r}
lr_drop_time = {lr_drop_time!r}
lr_final = {lr_final!r}

_anneal_start_time = [None]  # mutable container to share across methods

_OrigPuffeRL = pufferl_module.PuffeRL
class _PatchedPuffeRL(_OrigPuffeRL):
    def __init__(self, train_args, *args, **kwargs):
        _anneal_start_time[0] = _time_module.time()
        train_args['learning_rate'] = lr_warmup_start  # start at warmup LR
        train_args['gamma'] = gamma
        train_args['bptt_horizon'] = bptt_horizon
        train_args['gae_lambda'] = gae_lambda
        train_args['ent_coef'] = ent_start  # start at high entropy
        train_args['clip_coef'] = 0.2  # best clip_coef from prior sessions
        train_args['vf_coef'] = 0.5
        train_args['update_epochs'] = 1
        train_args['max_grad_norm'] = 1.5  # back to cogames default (0.5 tested → 136j, worse)
        train_args['adam_beta1'] = 0.95  # restore cogames default (0.9 tested → 240.8j, worse)
        super().__init__(train_args, *args, **kwargs)

    def train(self):
        # Constant LR (step LR and cosine LR both failed)
        self.config["learning_rate"] = learning_rate
        # Constant entropy (no annealing — all annealing variants fail)
        if _anneal_start_time[0] is not None:
            frac = min(1.0, (_time_module.time() - _anneal_start_time[0]) / anneal_duration)
            new_ent = ent_start + frac * (ent_end - ent_start)
            self.config["ent_coef"] = new_ent
        return super().train()

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
    checkpoint_interval=50,  # save less frequently to avoid disk quota issues (was 10)
    vector_num_envs={vector_num_envs!r},
    vector_batch_size={vector_batch_size!r},
    vector_num_workers={vector_num_workers!r},
)
"""


def build_train_command(bptt_override=None, initial_weights_path=None, time_budget_override=None):
    """Build the training command using cogames Python API (supports reward variants).

    Args:
        bptt_override: Override BPTT_HORIZON (for two-phase training).
        initial_weights_path: Path to checkpoint to load (for Phase 2 warm-start).
        time_budget_override: Override TIME_BUDGET for annealing duration.
    """
    bptt = bptt_override if bptt_override is not None else BPTT_HORIZON
    budget = time_budget_override if time_budget_override is not None else TIME_BUDGET
    # If loading from checkpoint, add data= to policy spec
    policy = f"{POLICY},data={initial_weights_path}" if initial_weights_path else POLICY
    script = TRAIN_SCRIPT.format(
        mission=MISSION,
        reward_variants=REWARD_VARIANTS,
        policy=policy,
        device=DEVICE,
        num_steps=NUM_STEPS,
        minibatch_size=MINIBATCH_SIZE,
        checkpoints="./train_dir",
        learning_rate=LEARNING_RATE,
        lr_warmup_start=LR_WARMUP_START,
        lr_warmup_duration=LR_WARMUP_DURATION,
        value_lr=VALUE_LR,
        gamma=GAMMA,
        bptt_horizon=bptt,
        gae_lambda=GAE_LAMBDA,
        ent_start=ENT_COEF_START,
        ent_end=ENT_COEF_END,
        vector_num_envs=VECTOR_NUM_ENVS,
        vector_batch_size=VECTOR_BATCH_SIZE,
        vector_num_workers=VECTOR_NUM_WORKERS,
        time_budget=budget,
        lr_drop_time=LR_DROP_TIME,
        lr_final=LR_FINAL,
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
    game_metrics=None, e2e_seconds=0.0,
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
                    "session_tokens_cumulative",
                    "session_cost_cumulative",
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
                ""  # api_cost_usd — filled by agent,
                "",  # session_tokens_cumulative — filled by agent
                "",  # session_cost_cumulative — filled by agent
            ]
            + [f"{v:.1f}" for v in game_metrics.values()]
        )


def run_training_phase(cmd, budget, phase_label):
    """Run a training subprocess for up to `budget` seconds, streaming output.
    Returns (output_lines, returncode)."""
    t_phase = time.time()
    output_lines = []
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        for line in iter(process.stdout.readline, ""):
            line = line.rstrip("\n")
            output_lines.append(line)
            print(line, flush=True)
            if time.time() - t_phase > budget:
                print(f"\n[{phase_label} TIME BUDGET] {budget}s exceeded, stopping...")
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
    return output_lines, returncode


def main():
    experiment_start_time = time.time()

    print("=" * 60)
    print("CoGames Autoresearch Training")
    print("=" * 60)
    print(f"Mission:          {MISSION}")
    print(f"Policy:           {POLICY}")
    print(f"Reward variants:  {REWARD_VARIANTS}")
    print(f"Learning rate:    {LEARNING_RATE}")
    print(f"Minibatch size:   {MINIBATCH_SIZE}")
    print(f"BPTT:             {BPTT_HORIZON}")
    print(f"Time budget:      {TIME_BUDGET}s")
    print(f"Device:           {DEVICE}")
    print("=" * 60)

    cmd = build_train_command()
    output_lines, returncode = run_training_phase(cmd, TIME_BUDGET, "MAIN")
    training_seconds = time.time() - experiment_start_time

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

    print(f"e2e_seconds:      {e2e_seconds:.1f}")
    print(f"timestamp:        {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}")

    log_to_results_tsv(
        commit, composite_score, mean_reward, memory_gb, status, DESCRIPTION,
        game_metrics=game_metrics,
        e2e_seconds=e2e_seconds,
    )
    print(
        f"\nLogged to results.tsv: {commit} | {composite_score:.6f} | {status} | {DESCRIPTION}"
    )


if __name__ == "__main__":
    main()
