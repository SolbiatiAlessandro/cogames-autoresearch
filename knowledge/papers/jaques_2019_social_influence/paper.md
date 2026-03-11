# Social Influence as Intrinsic Motivation for Multi-Agent Deep Reinforcement Learning

**Authors:** Natasha Jaques, Angeliki Lazaridou, Edward Hughes, Caglar Gulcehre, Pedro A. Ortega, DJ Strouse, Joel Z. Leibo, Nando de Freitas

**Year / Venue:** ICML 2019 — Best Paper Honourable Mention (top 0.26% of submissions)

**arXiv:** [1810.08647](https://arxiv.org/abs/1810.08647)

---

## Abstract

We propose a mechanism for achieving coordination and communication in multi-agent reinforcement learning (MARL) by rewarding agents for having causal influence over other agents' actions. Causal influence is assessed using counterfactual reasoning: at each timestep, an agent simulates alternate actions it could have taken and computes their effect on the behavior of other agents. Actions that lead to bigger changes in other agents' behavior are considered influential and are rewarded. We show that this is equivalent to rewarding agents for having high mutual information between their actions. The influence rewards for all agents can be computed in a decentralized way, enabling agents to learn a model of other agents using deep neural networks. Empirical results demonstrate that influence leads to enhanced coordination and communication in challenging social dilemma environments.

---

## Introduction

Human society depends critically on the ability to influence and be influenced by others. The authors ask: can agents be intrinsically motivated to influence one another, and will this give rise to emergent coordination and communication?

Prior work on emergent communication generally required centralized training — sharing gradients or reward signals across agents. This approach introduces a general, decentralized, domain-agnostic motivation signal: **causal social influence**.

---

## Methods

### Causal Influence Reward

At each timestep, agent *k* computes an **influence reward** over co-agents *j* by comparing agent *j*'s action distribution under the actual action vs. counterfactual alternate actions. If the actual action causes a larger change in agent *j*'s behavior, it is rewarded. Across many trajectories, this computes a Monte Carlo estimate of:

```
Reward_influence(k) = I(a_k ; a_j | s)
```

i.e., the **mutual information** between agents *k* and *j*'s actions.

### Model of Other Agents (MOA)

Each agent maintains a **Model of Other Agents (MOA)** — a neural network trained via supervised behavioral cloning to predict other agents' actions given current observations. The MOA enables decentralized computation of the influence reward without centralized training.

### Communication Channel

When a communication channel is provided, agents broadcast a discrete symbol to all other agents each timestep. The influence reward incentivizes agents to use the channel meaningfully: sending symbols that change other agents' behavior is rewarded.

### Training & Environments

- **Algorithm:** A3C with LSTM policy
- **Environments:** Sequential Social Dilemmas (SSDs)
  - **Harvest:** Tragedy-of-the-commons apple harvesting — over-harvesting collapses the shared resource
  - **Cleanup:** Public goods dilemma — agents must clean a river to maintain apple production but can free-ride

---

## Key Results

- Influence-trained agents **substantially outperform** A3C baselines in both Cleanup and Harvest collective reward
- In Harvest, baseline A3C fails to coordinate; influence agents learn sustainable harvesting
- With a communication channel, influence agents learn **non-trivial communication protocols** correlated with intended actions
- Baseline A3C agents with communication channels fail to learn meaningful protocols
- Decentralized influence approach matches or exceeds centralized training methods

### Ablations

Both counterfactual reasoning and the MOA are critical — removing either significantly degrades performance.

---

## Conclusion

**Causal social influence** — rewarding agents for measurably affecting others' behavior — is a powerful, general intrinsic motivation for multi-agent systems:

1. A single influence reward promotes both implicit coordination and explicit communication
2. Information-theoretic grounding: equivalent to maximizing mutual information between agents' actions
3. Fully decentralized via a learned Model of Other Agents
4. Influence-motivated agents develop structured communication protocols and coordinated resource use that baseline RL agents never produce

---

## Links

- **arXiv:** https://arxiv.org/abs/1810.08647
- **ICML Proceedings:** https://proceedings.mlr.press/v97/jaques19a.html
