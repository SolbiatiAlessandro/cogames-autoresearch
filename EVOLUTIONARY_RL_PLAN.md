# Evolutionary RL Approach for CoGames

## Problem We're Solving

**Policy drift in on-policy RL (PPO/MAPPO):**
- Single agent: 73.2 (10-min) → 58.6 (30-min)
- Value instability leads to conservative behavior
- Agent "forgets" aggressive strategies that win
- No mechanism to preserve successful behaviors

## Solution: Population-Based Training (PBT)

### Core Idea
Train **multiple agents in parallel** from the best checkpoint:
- Each starts from epoch 330 (score 73.2) with different hyperparameters
- Periodically evaluate all agents
- Underperformers copy parameters from top performers
- All agents explore via hyperparameter perturbations

### Why This Works for Our Case

1. **Preserves Good Behaviors**
   - Top performers maintain aggressive strategies
   - Underperformers can "reset" to working policies
   - Population retains diverse approaches

2. **Addresses Value Instability**
   - Different value LRs across population
   - Find optimal critic speed automatically
   - Reduces dependence on single trajectory

3. **Handles Policy Drift**
   - Drift happens → agent falls behind → copies from winner
   - Winners stay aggressive (high score)
   - Losers (conservative) get replaced

4. **Hyperparameter Discovery**
   - Automatically finds best LR, entropy, GAE, etc.
   - No manual grid search needed
   - Adapts to training stage

## Concrete Implementation Plan

### Phase 1: Simple PBT (4-8 agents)

**Setup:**
```python
Population = 8 agents
Base checkpoint = epoch 330 (score 73.2)

Initial hyperparameters (uniform random in ranges):
- policy_lr: [0.0003, 0.001, 0.003]
- value_lr: [0.0001, 0.0003, 0.001]
- entropy_coef: [0.10, 0.15, 0.20]
- gae_lambda: [0.90, 0.95, 0.98]
```

**Training loop:**
```
1. All agents train for 5 minutes (parallel on single GPU)
2. Evaluate all agents (get composite scores)
3. Selection:
   - Bottom 25% (2 agents) copy params from top 25%
   - Also copy hyperparameters
4. Perturbation:
   - All agents perturb hyperparameters ±20%
   - Keep within valid ranges
5. Repeat for N cycles (e.g., 6 cycles = 30 min total)
```

**Benefits:**
- Runs on single machine (sequential or vectorized)
- Low overhead (checkpoint saves + evals)
- Automatically finds stable hyperparameters
- Best agent likely maintains 73.2+ score

### Phase 2: Evolutionary Search Extensions

**If Phase 1 works, add:**

1. **Mutation operators:**
   - Learning rate schedules (cosine, step decay)
   - Architecture changes (hidden size, layers)
   - Reward variant combinations

2. **Crossover:**
   - Mix parameters from two good agents
   - E.g., policy from Agent A, value function from Agent B

3. **Speciation:**
   - Cluster agents by behavior (aggressive vs defensive)
   - Maintain diversity explicitly
   - Prevent convergence to single strategy

4. **Multi-objective:**
   - Optimize for: score, exploration, resource efficiency
   - Pareto frontier of policies
   - User picks based on preference

### Phase 3: Advanced (if needed)

**For very long training:**

1. **Behavioral Cloning Loss:**
   - Add loss term: KL(π_current || π_epoch330)
   - Prevents drift from original good policy
   - Weight: 0.1-0.5 of policy loss

2. **Experience Replay Buffer:**
   - Store rollouts from top performers
   - Periodically train on old successful trajectories
   - Prevents forgetting good behaviors

3. **Multi-Stage Training:**
   - Stage 1: Explore (high entropy, diverse strategies)
   - Stage 2: Exploit (low entropy, refine best)
   - Stage 3: Stabilize (BC loss + replay)

## Implementation Roadmap

### Week 1: Proof of Concept
```
Day 1-2: Implement basic PBT infrastructure
- Population manager (launch/stop agents)
- Evaluation harness (score all agents)
- Selection/perturbation logic

Day 3-4: Run first PBT experiment
- 8 agents, 6 cycles (30 min total)
- Compare best agent vs baseline (73.2)
- Track diversity (different strategies?)

Day 5: Analysis & iteration
- Did we maintain score? Improve?
- Which hyperparameters worked best?
- Did population retain aggressive behavior?
```

### Week 2: Refinement
```
- Tune selection pressure (25% → 10%? 50%?)
- Add learning rate schedules
- Try larger population (16 agents)
- Longer cycles (10 min each)
```

## Expected Outcomes

**Success criteria:**
1. ✅ Best agent maintains 73+ score after 30+ min training
2. ✅ Population diversity (not all agents converge to same policy)
3. ✅ Automatic hyperparameter discovery (better than manual tuning)

**Possible results:**

**Best case:** Population finds stable config that maintains 73+ indefinitely
- Some agents explore, others exploit
- Top performer never drifts conservative
- **Next step:** Scale to longer training, deploy winner

**Moderate case:** Population maintains 70-72 (better than 58.6)
- Drift reduced but not eliminated
- Need BC loss or replay buffer
- **Next step:** Add Phase 3 techniques

**Worst case:** All agents drift to 58-60 despite PBT
- Problem is deeper than hyperparameters
- On-policy RL fundamentally unstable for this task
- **Next step:** Switch to off-policy (SAC/TD3) or different architecture

## Code Sketch

```python
# pbt_manager.py
class PBTPopulation:
    def __init__(self, base_checkpoint, pop_size=8):
        self.agents = [
            Agent(
                checkpoint=base_checkpoint,
                policy_lr=random.uniform(0.0003, 0.003),
                value_lr=random.uniform(0.0001, 0.001),
                entropy=random.uniform(0.10, 0.20),
            )
            for _ in range(pop_size)
        ]
    
    def train_cycle(self, minutes=5):
        """Train all agents for N minutes in parallel"""
        for agent in self.agents:
            agent.train(time_budget=minutes*60)
    
    def evaluate_all(self):
        """Get scores for all agents"""
        return [agent.evaluate() for agent in self.agents]
    
    def select_and_replace(self, scores):
        """Bottom 25% copy from top 25%"""
        sorted_agents = sorted(zip(scores, self.agents), reverse=True)
        top_25 = sorted_agents[:len(self.agents)//4]
        bottom_25_idx = sorted(range(len(scores)), key=lambda i: scores[i])[:len(self.agents)//4]
        
        for idx in bottom_25_idx:
            winner = random.choice(top_25)[1]
            self.agents[idx].copy_from(winner)
    
    def perturb_hyperparameters(self):
        """All agents perturb hyperparams ±20%"""
        for agent in self.agents:
            agent.policy_lr *= random.uniform(0.8, 1.2)
            agent.value_lr *= random.uniform(0.8, 1.2)
            agent.entropy *= random.uniform(0.8, 1.2)
            agent.clamp_hyperparams()  # keep in valid range

# Main training loop
pop = PBTPopulation(base_checkpoint="epoch_330.pt", pop_size=8)

for cycle in range(6):  # 6 cycles × 5 min = 30 min
    print(f"Cycle {cycle+1}/6")
    pop.train_cycle(minutes=5)
    scores = pop.evaluate_all()
    print(f"Scores: {scores}")
    print(f"Best: {max(scores):.2f}, Worst: {min(scores):.2f}")
    
    pop.select_and_replace(scores)
    pop.perturb_hyperparameters()

# Final evaluation
final_scores = pop.evaluate_all()
best_agent = pop.agents[np.argmax(final_scores)]
print(f"Best agent score: {max(final_scores):.2f}")
best_agent.save("best_pbt_agent.pt")
```

## Resources

**Papers:**
- DeepMind PBT: https://deepmind.google/blog/population-based-training-of-neural-networks/
- EVO-PBT for PPO: https://github.com/yyzpiero/EVO-PopulationBasedTraining
- Poppy (specialized PBT): https://instadeep.com/2022/10/population-based-reinforcement-learning-for-combinatorial-optimization/

**Key insights:**
- PBT works on single machine with vectorization
- Winner-takes-all often better than truncation selection
- Minimal overhead if eval is fast
- Can parallelize across multiple GPUs if available

## Next Actions

1. ✅ **Finish current eval** (Exp 2 dual LR) to establish baseline
2. **Implement PBT manager** (~1-2 hours coding)
3. **Run first PBT experiment** (8 agents, 30 min)
4. **Compare:** PBT best vs baseline vs dual-LR
5. **Iterate:** Tune selection/perturbation based on results

---

**TL;DR:** Instead of training one agent that drifts, train 8 agents where underperformers copy winners. This should maintain aggressive behaviors and prevent conservative drift.
