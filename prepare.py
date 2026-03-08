"""
CoGames autoresearch evaluation harness. READ-ONLY — do not modify.

This file sets up the CoGames environment, defines the fixed evaluation
protocol, and provides the composite metric. The agent may only modify
train.py.

Usage:
    # Import from train.py:
    from prepare import TIME_BUDGET, MISSION, evaluate, make_env_config
"""

import time

# ---------------------------------------------------------------------------
# Constants (fixed, do not modify)
# ---------------------------------------------------------------------------

TIME_BUDGET = 600  # training time budget in seconds (10 minutes)
EVAL_EPISODES = 10  # number of evaluation episodes
MISSION = "cogsguard_machina_1.basic"  # mission to train on

# Smaller missions for faster iteration (agent can read but not change this):
# - "training_facility_open_1" — tiny map, 2 agents, ~30s per episode
# - "cogsguard_machina_1.basic" — standard benchmark, 4 agents

# ---------------------------------------------------------------------------
# Environment setup
# ---------------------------------------------------------------------------

def make_env_config(mission: str = MISSION, num_agents: int = 4):
    """Create a MettaGridConfig for the given mission.

    Returns the mission name and env config tuple, matching cogames CLI internals.
    """
    # TODO: Import from cogames and resolve mission config
    # from cogames.cli.mission import get_mission_name_and_config
    # This requires setting up the cogames CLI context properly.
    # For now, we use the cogames CLI directly via subprocess.
    raise NotImplementedError(
        "Direct config creation not yet implemented. "
        "Use `cogames tutorial train` CLI for now. "
        "See Task 1 in Notion for details."
    )


# ---------------------------------------------------------------------------
# Evaluation (DO NOT CHANGE — this is the fixed metric)
# ---------------------------------------------------------------------------

def evaluate(checkpoint_path: str, mission: str = MISSION, episodes: int = EVAL_EPISODES):
    """Run evaluation episodes and return composite score.

    The composite score is a single number (higher = better) that the
    autoresearch loop optimizes. It combines:
    - mean per-agent reward across episodes
    - bonus for coordination behaviors (deposit diversity, role specialization)

    Hard constraints (score = 0 if violated):
    - No NaN in any metric
    - Training must not have diverged

    Returns:
        dict with keys:
            composite_score: float  — the ONE number to optimize
            mean_reward: float      — average per-agent reward
            episodes: int           — number of eval episodes run
    """
    # TODO: Implement evaluation using cogames eval
    #
    # The approach:
    # 1. Load the checkpoint from checkpoint_path
    # 2. Run cogames eval: `cogames run -m {mission} -p {checkpoint} -e {episodes} --format json`
    # 3. Parse the JSON output to extract per-agent rewards
    # 4. Compute composite score
    #
    # For now, use subprocess to call cogames CLI:
    #
    # import subprocess, json
    # result = subprocess.run(
    #     ["cogames", "run", "-m", mission, "-p", checkpoint_path,
    #      "-e", str(episodes), "--format", "json"],
    #     capture_output=True, text=True
    # )
    # data = json.loads(result.stdout)
    # rewards = extract_rewards(data)
    # composite = compute_composite(rewards)
    #
    raise NotImplementedError(
        "Evaluation not yet implemented. "
        "See Task 1 in Notion for the full spec."
    )


def compute_composite_score(mean_reward: float, deposit_diversity: float = 0.0) -> float:
    """Compute the single optimization target.

    Formula: mean_reward * (1 + 0.5 * deposit_diversity)

    This rewards both raw performance AND coordination.
    deposit_diversity ranges from 0 (no diversity) to 1 (all resource types deposited).
    """
    return mean_reward * (1.0 + 0.5 * deposit_diversity)
