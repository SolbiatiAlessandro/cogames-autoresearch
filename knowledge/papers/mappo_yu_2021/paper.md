# The Surprising Effectiveness of PPO in Cooperative Multi-Agent Games (MAPPO)

**Authors:** Chao Yu, Akash Velu, Eugene Vinitsky, Jiaxuan Gao, Yu Wang, Alexandre Bayen, Yi Wu

**Year / Venue:** 2021 (arXiv); accepted at NeurIPS 2022 Datasets and Benchmarks Track

**arXiv ID:** [2103.01955](https://arxiv.org/abs/2103.01955)

---

## Abstract

Proximal Policy Optimization (PPO) has proven highly effective in single-agent reinforcement learning, yet the multi-agent reinforcement learning (MARL) community has largely overlooked it in favor of off-policy methods. This paper empirically demonstrates that PPO — with careful implementation — achieves competitive or superior performance relative to state-of-the-art off-policy algorithms across four cooperative multi-agent benchmarks: Multi-Agent Particle Environments (MPE), the StarCraft Multi-Agent Challenge (SMAC), Google Research Football (GRF), and the Hanabi challenge. These results hold in both final performance and sample efficiency, while requiring minimal hyperparameter tuning and no domain-specific algorithmic modifications. The authors identify five critical implementation factors that drive PPO's effectiveness in multi-agent cooperative settings.

---

## Introduction

The paper addresses a notable gap in the MARL literature. While high-profile systems such as OpenAI Five and AlphaStar achieved landmark results using on-policy methods (including PPO) at massive scale, recent academic MARL research has overwhelmingly focused on off-policy frameworks — particularly value decomposition Q-learning methods (e.g., QMix, QPlex) and MADDPG.

The authors hypothesize two root causes for this perception:
1. PPO's apparent lower sample efficiency compared to off-policy methods
2. A mismatch between standard single-agent PPO practices and the requirements of multi-agent environments

Rather than proposing a new algorithm, the paper conducts a rigorous empirical study to determine whether PPO, when properly configured, can serve as a strong baseline for cooperative MARL. Two variants are introduced:
- **MAPPO** (Multi-Agent PPO with a centralized critic)
- **IPPO** (Independent PPO with a decentralized critic)

---

## Methods

### Algorithm Variants

- **MAPPO:** Standard PPO with a *centralized value function* that takes in global state information during training but executes decentrally at test time. Follows the CTDE (centralized training, decentralized execution) paradigm.
- **IPPO:** Each agent runs its own PPO instance using only local observations — fully decentralized.

Both variants use **parameter sharing** across homogeneous agents.

### Five Critical Implementation Factors

1. **Value Normalization:** Normalizing value function targets using running statistics (mean and variance) stabilizes training across shifting reward distributions.

2. **Value Function Input Representation:** Four strategies compared:
   - *CL (Concatenated Local):* All agents' local observations concatenated — scales poorly.
   - *EP (Environment-Provided):* Global state from environment, omits agent-specific details.
   - *AS (Agent-Specific):* EP state + individual agent's local observation — generally best.
   - *FP (Feature-Pruned):* AS with redundant features removed — also strong.

3. **Training Data Usage:** Multi-agent settings benefit from fewer training epochs (5–10 for hard tasks) and minimal mini-batching (ideally 1 mini-batch per rollout). Excessive data reuse hurts due to multi-agent non-stationarity.

4. **Policy and Value Clipping:** PPO clipping coefficient ε should be ≤ 0.2. Higher values cause suboptimal learning.

5. **Batch Size:** There exists a minimum batch size threshold below which performance degrades. Find the minimum sufficient batch size, then tune for sample efficiency.

---

## Key Results

| Benchmark | Finding |
|---|---|
| **MPE** (Spread, Reference, Comm) | MAPPO matches or exceeds QMix and MADDPG on all three tasks |
| **SMAC** (23 maps) | MAPPO and IPPO match or exceed QMix on the vast majority of maps |
| **Google Research Football** | MAPPO substantially outperforms QMix (e.g., 88% vs. 8% on 3v.1) |
| **Hanabi** (2–5 players) | MAPPO matches or exceeds SAD and VDN across player counts |

**Overall:** Properly configured PPO matches or surpasses state-of-the-art off-policy methods across all four benchmarks, without task-specific algorithmic modifications.

---

## Conclusion

MAPPO establishes that **PPO is a strong and competitive baseline for cooperative MARL**. The five identified implementation factors explain why prior comparisons may have underestimated PPO's potential. This is primarily an empirical contribution providing practical guidance rather than algorithmic novelty.

Limitations and future directions:
- All benchmarks use discrete action spaces; extension to continuous actions is future work
- All settings are cooperative; competitive or mixed settings not addressed
- Primarily homogeneous agents; heterogeneous settings need further study

---

## Links

- **arXiv:** https://arxiv.org/abs/2103.01955
- **Code:** https://github.com/marlbenchmark/on-policy
