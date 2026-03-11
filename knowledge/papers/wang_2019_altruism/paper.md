# Evolving Intrinsic Motivations for Altruistic Behavior

**Authors:** Jane X. Wang, Edward Hughes, Chrisantha Fernando, Wojciech M. Czarnecki, Edgar A. Duenez-Guzman, Joel Z. Leibo

**Year / Venue:** AAMAS 2019 (Montreal, May 13–17, 2019)

**arXiv:** [1811.05931](https://arxiv.org/abs/1811.05931)

**Affiliation:** DeepMind

---

## Abstract

Many tasks involve individual incentives that are misaligned with the common good, yet a wide range of organisms are able to overcome their differences and collaborate. By combining MARL with appropriately structured natural selection, the authors demonstrate that individual inductive biases for cooperation can be learned in a model-free way. They introduce a modular architecture for deep RL agents that supports multi-level selection, demonstrating results across two challenging environments.

---

## Introduction

This paper studies **intertemporal social dilemmas (ISDs)**: multi-player games where short-term selfish actions produce individual benefit but long-term costs for the group. Classic examples include the Prisoner's Dilemma and commons-harvesting scenarios.

Prior approaches require domain knowledge or manual design (opponent modeling, hand-crafted intrinsic motivations from behavioral economics). The authors propose that **evolution can automatically discover intrinsic motivations** — replacing hand-crafted social preferences with evolved reward network weights.

Key conceptual innovation: a separation of two timescales:
- **Fast timescale:** Within-lifetime reinforcement learning (policy optimization)
- **Slow timescale:** Cross-generation evolution (reward network optimization)

---

## Methods

### Environments (N = 5 agents)

- **Cleanup:** Agents must collectively clean a polluted aquifer to maintain apple spawn rates. Individual temptation: skip cleaning and free-ride on others' effort.
- **Harvest:** Apple regrowth depends on local density. Individual incentive: greedily harvest, but over-harvesting collapses the shared resource.

Both games feature optional "tagging" (penalize others at a cost to self).

### Agent Architecture

Each agent's total reward = **extrinsic** (environment) + **intrinsic** (small 2-layer neural network with 2 hidden nodes).

The intrinsic network takes features derived from other agents' rewards as input. Two variants:
- **Retrospective:** Intrinsic reward based on whether others were recently rewarded (consequentialist)
- **Prospective:** Intrinsic reward based on whether others are expected to be rewarded soon (intentional)

### Multi-Level Selection via Shared Reward Networks

The central innovation: **a single reward network is shared by all players in an episode**.

After each episode:
- **Policy networks** evolve according to individual returns
- **Reward networks** evolve according to the **aggregate return across all players**

This implements biological multi-level selection: policies selected for individual fitness, reward signals selected for group fitness. Prevents reward networks from being co-opted for purely selfish ends.

### Matchmaking

- **Random matchmaking:** Agents sampled uniformly at random
- **Assortative matchmaking (Greenbeard strategy):** Cooperative agents paired with cooperators; defectors with defectors. Operationalizes biological "Greenbeard" mechanism — honest cooperativeness signals enable preferential association.

### Training

- Population of 50 policy networks, 500 parallel episodes per generation
- V-Trace off-policy actor-critic learning
- Population-Based Training (PBT) for hyperparameter evolution

---

## Key Results

| Condition | Outcome |
|---|---|
| PBT baseline (no intrinsic reward) | Fails in both games (0 total reward in Cleanup) |
| Individual reward networks + random matchmaking | Minimal improvement — evolve selfishly |
| Assortative matchmaking + individual networks | High performance where honest signals available |
| **Shared reward networks + random matchmaking** | Matches hand-crafted approaches without domain-specific engineering |

**Social outcome metrics (shared reward networks):**
- **Equality:** Very high Gini equality in Harvest
- **Tagging:** Substantially less inter-agent punishment than other variants
- **Sustainability:** More sustainable resource management

### Evolved Reward Weights

Weights differ between games, suggesting different social preferences are appropriate for different dilemma structures. Harvest requires more complex, opposing weight values.

---

## Conclusion

Three main conclusions:

1. **Naive genetic algorithms fail:** Random interaction without structured dynamics doesn't produce cooperative behavior
2. **Assortative matchmaking is sufficient when honest signals exist:** Preferential association with cooperators drives altruism naturally
3. **Multi-level selection via shared reward networks generalizes:** Works in general settings without honest signals or assortative dynamics

Evolution "ameliorates the intertemporal choice problem by distilling the long timescale of collective fitness into the short timescale of individual reinforcement learning." Intrinsic motivations that evolve to improve group outcomes compress slow evolutionary credit assignment into fast per-episode learning signals.

Connection to biological analogues: slime mold multicellularity, horizontal gene transfer, human cultural norms that spread independently of individual survival.

---

## Links

- **arXiv:** https://arxiv.org/abs/1811.05931
- **AAMAS 2019 PDF:** https://www.ifaamas.org/Proceedings/aamas2019/pdfs/p683.pdf
- **DeepMind publication:** https://deepmind.google/publications/evolving-intrinsic-motivations-for-altruistic-behavior
