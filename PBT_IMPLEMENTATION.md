# Population-Based Training - Implementation Guide

## Quick Start

**Goal:** Train 8 agents in parallel, where underperformers copy from winners, to maintain aggressive behavior and prevent policy drift.

**Expected outcome:** Best agent maintains 73+ score after 30+ minutes (vs 58.6 baseline degradation)

## Step 1: Create PBT Manager (~30 min)

```bash
cd /workspace/repos/cogames-autoresearch
mkdir -p pbt
```

Create `pbt/manager.py`:

```python
#!/usr/bin/env python3
"""Population-Based Training Manager for CoGames"""
import random
import time
import json
from pathlib import Path
from typing import List, Dict
import subprocess
import numpy as np

class Agent:
    """Single agent in the population"""
    def __init__(self, agent_id: int, base_checkpoint: str, work_dir: Path):
        self.id = agent_id
        self.work_dir = work_dir / f"agent_{agent_id}"
        self.work_dir.mkdir(exist_ok=True)
        
        # Initialize hyperparameters (random in range)
        self.policy_lr = random.uniform(0.0003, 0.003)
        self.value_lr = random.uniform(0.0001, 0.001)
        self.entropy_coef = random.uniform(0.12, 0.20)
        self.gae_lambda = random.choice([0.90, 0.95, 0.98])
        
        # Copy base checkpoint
        self.checkpoint = self.work_dir / "current.pt"
        subprocess.run(["cp", base_checkpoint, str(self.checkpoint)], check=True)
        
        # Training state
        self.score = 0.0
        self.generation = 0
        
    def train(self, time_budget: int = 300):
        """Train agent for N seconds"""
        log_file = self.work_dir / f"train_gen{self.generation}.log"
        
        cmd = f"""
        cd /workspace/repos/cogames-autoresearch
        source .env.sh
        uv run python -c "
import time
from pathlib import Path
from cogames.cli.mission import get_mission
from cogames.cli.policy import parse_policy_spec
from cogames.cogs_vs_clips.reward_variants import apply_reward_variants
from cogames.device import resolve_training_device
from rich.console import Console
import pufferlib.pufferl as pufferl_module
import cogames.train as train_module

mission = 'cogsguard_machina_1.basic'
reward_variants = ['milestones_2:25', 'role_conditional', 'penalize_vibe_change']
policy_str = 'class=lstm,kw.hidden_size=256'

# Hyperparameters for this agent
POLICY_LR = {self.policy_lr}
VALUE_LR = {self.value_lr}
ENT_COEF = {self.entropy_coef}
GAE_LAMBDA = {self.gae_lambda}
TIME_BUDGET = {time_budget}

# Patch PuffeRL
_Orig = pufferl_module.PuffeRL
class _TimedPuffeRL(_Orig):
    def __init__(self, train_args, *args, **kwargs):
        train_args['learning_rate'] = POLICY_LR
        train_args['gamma'] = 0.999
        train_args['bptt_horizon'] = 128
        train_args['gae_lambda'] = GAE_LAMBDA
        train_args['ent_coef'] = ENT_COEF
        train_args['clip_coef'] = 0.2
        train_args['vf_coef'] = 0.5
        train_args['update_epochs'] = 1
        super().__init__(train_args, *args, **kwargs)
        
        # Dual LR setup
        policy_params = []
        value_params = []
        for name, param in self.policy.named_parameters():
            if 'critic' in name.lower() or 'value' in name.lower() or 'vf' in name.lower():
                value_params.append(param)
            else:
                policy_params.append(param)
        
        self.optimizer = type(self.optimizer)([
            {{'params': policy_params, 'lr': POLICY_LR}},
            {{'params': value_params, 'lr': VALUE_LR}}
        ])
        
        self.start_time = time.time()
        
    def evaluate(self):
        if time.time() - self.start_time > TIME_BUDGET:
            raise KeyboardInterrupt('Time budget')
        return super().evaluate()

pufferl_module.PuffeRL = _TimedPuffeRL

name, env_cfg, _ = get_mission(mission)
apply_reward_variants(env_cfg, variants=reward_variants)
policy_spec = parse_policy_spec(policy_str)
console = Console()
device = resolve_training_device(console, 'auto')

try:
    train_module.train(
        env_cfg=env_cfg,
        policy_class_path=policy_spec.class_path,
        initial_weights_path='{self.checkpoint}',
        device=device,
        num_steps=10_000_000_000,
        checkpoints_path=Path('{self.work_dir}/checkpoints'),
        seed=42,
        minibatch_size=8192,
        log_outputs=True,
        checkpoint_interval=999,
        vector_num_envs=64,
        vector_num_workers=8,
    )
except KeyboardInterrupt:
    print('Training complete')
" 2>&1 | tee {log_file}
        """
        
        subprocess.run(cmd, shell=True, check=True)
        self.generation += 1
        
        # Update checkpoint to latest
        latest_ckpt = self.work_dir / "checkpoints" / "*.pt"
        # TODO: find latest checkpoint and copy to self.checkpoint
        
    def evaluate(self) -> float:
        """Evaluate agent and return score"""
        # TODO: Run proper evaluation
        # For now, parse score from log file
        log_file = self.work_dir / f"train_gen{self.generation-1}.log"
        score = self._parse_score_from_log(log_file)
        self.score = score
        return score
    
    def _parse_score_from_log(self, log_file: Path) -> float:
        """Extract composite score from training log"""
        try:
            with open(log_file) as f:
                for line in f:
                    if "composite_score:" in line:
                        return float(line.split("composite_score:")[1].strip().split()[0])
        except:
            pass
        return 0.0
    
    def copy_from(self, other: 'Agent'):
        """Copy parameters and hyperparameters from another agent"""
        subprocess.run(["cp", str(other.checkpoint), str(self.checkpoint)], check=True)
        self.policy_lr = other.policy_lr
        self.value_lr = other.value_lr
        self.entropy_coef = other.entropy_coef
        self.gae_lambda = other.gae_lambda
        print(f"  Agent {self.id} copied from Agent {other.id}")
    
    def perturb_hyperparameters(self):
        """Randomly perturb hyperparameters ±20%"""
        self.policy_lr *= random.uniform(0.8, 1.2)
        self.value_lr *= random.uniform(0.8, 1.2)
        self.entropy_coef *= random.uniform(0.8, 1.2)
        
        # Clamp to valid ranges
        self.policy_lr = np.clip(self.policy_lr, 0.0001, 0.01)
        self.value_lr = np.clip(self.value_lr, 0.00005, 0.005)
        self.entropy_coef = np.clip(self.entropy_coef, 0.05, 0.30)
        
    def to_dict(self) -> Dict:
        """Serialize agent state"""
        return {
            'id': self.id,
            'policy_lr': self.policy_lr,
            'value_lr': self.value_lr,
            'entropy_coef': self.entropy_coef,
            'gae_lambda': self.gae_lambda,
            'score': self.score,
            'generation': self.generation,
        }


class PBTPopulation:
    """Population-Based Training manager"""
    def __init__(
        self,
        base_checkpoint: str,
        pop_size: int = 8,
        work_dir: str = "pbt_run",
    ):
        self.pop_size = pop_size
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(exist_ok=True)
        
        print(f"Initializing population of {pop_size} agents...")
        self.agents = [
            Agent(i, base_checkpoint, self.work_dir)
            for i in range(pop_size)
        ]
        
        # Log initial hyperparameters
        self._log_population(0)
        
    def train_cycle(self, minutes: int = 5):
        """Train all agents for N minutes"""
        print(f"\n{'='*60}")
        print(f"Training all agents for {minutes} minutes...")
        print(f"{'='*60}")
        
        time_budget = minutes * 60
        for i, agent in enumerate(self.agents):
            print(f"\nAgent {i}/{len(self.agents)}: Training...")
            print(f"  policy_lr={agent.policy_lr:.4f}, value_lr={agent.value_lr:.4f}")
            print(f"  entropy={agent.entropy_coef:.3f}, gae_lambda={agent.gae_lambda:.2f}")
            agent.train(time_budget)
            
    def evaluate_all(self) -> List[float]:
        """Evaluate all agents and return scores"""
        print(f"\n{'='*60}")
        print("Evaluating all agents...")
        print(f"{'='*60}")
        
        scores = []
        for i, agent in enumerate(self.agents):
            score = agent.evaluate()
            scores.append(score)
            print(f"Agent {i}: {score:.2f}")
            
        return scores
    
    def select_and_replace(self, scores: List[float]):
        """Bottom 25% copy from top 25%"""
        n_replace = max(1, self.pop_size // 4)
        
        # Find top and bottom performers
        sorted_indices = np.argsort(scores)[::-1]  # descending
        top_indices = sorted_indices[:n_replace]
        bottom_indices = sorted_indices[-n_replace:]
        
        print(f"\n{'='*60}")
        print(f"Selection: Bottom {n_replace} copy from top {n_replace}")
        print(f"{'='*60}")
        print(f"Top agents: {[f'Agent {i} ({scores[i]:.2f})' for i in top_indices]}")
        print(f"Bottom agents: {[f'Agent {i} ({scores[i]:.2f})' for i in bottom_indices]}")
        
        for bottom_idx in bottom_indices:
            top_idx = random.choice(top_indices)
            self.agents[bottom_idx].copy_from(self.agents[top_idx])
            
    def perturb_all(self):
        """All agents perturb hyperparameters"""
        print(f"\nPerturbing hyperparameters...")
        for agent in self.agents:
            agent.perturb_hyperparameters()
            
    def run(self, num_cycles: int = 6, minutes_per_cycle: int = 5):
        """Run full PBT training"""
        print(f"\n{'='*60}")
        print(f"Starting PBT: {num_cycles} cycles × {minutes_per_cycle} min")
        print(f"Total time: {num_cycles * minutes_per_cycle} minutes")
        print(f"{'='*60}\n")
        
        for cycle in range(1, num_cycles + 1):
            print(f"\n{'#'*60}")
            print(f"# CYCLE {cycle}/{num_cycles}")
            print(f"{'#'*60}")
            
            self.train_cycle(minutes=minutes_per_cycle)
            scores = self.evaluate_all()
            
            print(f"\nCycle {cycle} Summary:")
            print(f"  Best:  {max(scores):.2f}")
            print(f"  Mean:  {np.mean(scores):.2f}")
            print(f"  Worst: {min(scores):.2f}")
            
            self._log_population(cycle, scores)
            
            if cycle < num_cycles:
                self.select_and_replace(scores)
                self.perturb_all()
                
        # Final results
        print(f"\n{'='*60}")
        print("PBT COMPLETE!")
        print(f"{'='*60}")
        final_scores = self.evaluate_all()
        best_idx = np.argmax(final_scores)
        best_agent = self.agents[best_idx]
        
        print(f"\nBest agent: Agent {best_idx}")
        print(f"  Score: {final_scores[best_idx]:.2f}")
        print(f"  policy_lr={best_agent.policy_lr:.4f}")
        print(f"  value_lr={best_agent.value_lr:.4f}")
        print(f"  entropy={best_agent.entropy_coef:.3f}")
        print(f"  gae_lambda={best_agent.gae_lambda:.2f}")
        
        # Save best agent
        best_checkpoint = self.work_dir / "best_agent.pt"
        subprocess.run(["cp", str(best_agent.checkpoint), str(best_checkpoint)], check=True)
        print(f"\nBest checkpoint saved: {best_checkpoint}")
        
        return best_agent, final_scores
    
    def _log_population(self, cycle: int, scores: List[float] = None):
        """Log population state"""
        log_file = self.work_dir / f"population_cycle{cycle}.json"
        data = {
            'cycle': cycle,
            'agents': [agent.to_dict() for agent in self.agents],
        }
        if scores:
            data['scores'] = scores
        
        with open(log_file, 'w') as f:
            json.dump(data, f, indent=2)


if __name__ == "__main__":
    # Example usage
    pop = PBTPopulation(
        base_checkpoint="train_dir/177380707233/model_000330.pt",
        pop_size=8,
        work_dir="pbt_run_001"
    )
    
    best_agent, final_scores = pop.run(
        num_cycles=6,
        minutes_per_cycle=5
    )
```

## Step 2: Run First PBT Experiment

```bash
cd /workspace/repos/cogames-autoresearch
mkdir -p pbt

# Create the manager script
# (copy the code above)

# Run PBT
python3 pbt/manager.py
```

**This will:**
1. Initialize 8 agents from best checkpoint (epoch 330, score 73.2)
2. Each with random hyperparameters (policy_lr, value_lr, entropy, gae_lambda)
3. Train all agents for 5 minutes
4. Evaluate and rank by composite score
5. Bottom 2 copy from top 2
6. All perturb hyperparameters ±20%
7. Repeat for 6 cycles (30 minutes total)

## Step 3: Analyze Results

After completion, check:

```bash
# Best agent checkpoint
ls pbt_run_001/best_agent.pt

# Population logs
cat pbt_run_001/population_cycle*.json

# Training logs for each agent
ls pbt_run_001/agent_*/train_gen*.log
```

**Success criteria:**
- Best agent score ≥ 73 after 30 min
- Population diversity (different hyperparameters)
- Top agents maintain high entropy (>0.15)

## Step 4: Iteration

If results are promising:

1. **Run longer:** 12 cycles × 5 min = 1 hour
2. **Larger population:** 16 agents
3. **Add mutations:**
   - Architecture (hidden_size)
   - Reward variants
   - Learning rate schedules

If results are mixed:

1. **Stronger selection:** Replace bottom 50% instead of 25%
2. **Add behavioral cloning:** BC loss toward epoch 330 checkpoint
3. **Explicit entropy constraint:** Penalize agents with entropy < 0.14

## Expected Timeline

- **Implementation:** 30-60 min
- **First run:** 30 min (6 cycles × 5 min)
- **Analysis:** 15 min
- **Iteration:** 1-2 hours

**Total:** ~3-4 hours to proof-of-concept

## Troubleshooting

**Issue:** Agents crash during training
- Check logs in `pbt_run_001/agent_X/train_genY.log`
- Add error handling in `Agent.train()`

**Issue:** All agents converge to same hyperparameters
- Increase perturbation range (±30% instead of ±20%)
- Add exploration bonus for diversity

**Issue:** Scores don't improve
- The problem might be deeper than hyperparameters
- Try adding BC loss or experience replay (see EVOLUTIONARY_RL_PLAN.md Phase 3)

## Next Steps After PBT

If PBT successfully maintains score:
- Scale to longer training (2-4 hours)
- Deploy best agent
- Write up findings

If PBT doesn't work:
- Try Phase 3 techniques (BC loss, replay buffer)
- Consider off-policy algorithms (SAC, TD3)
- Investigate reward shaping (explicit penalties for passivity)

---

**Key insight:** PBT naturally selects for agents that maintain both value stability AND high exploration, which single-agent training cannot achieve.
