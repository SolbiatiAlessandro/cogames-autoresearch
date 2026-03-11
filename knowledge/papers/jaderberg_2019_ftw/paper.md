# Human-level performance in 3D multiplayer games with population-based reinforcement learning (FTW)

**Authors:** Max Jaderberg, Wojciech M. Czarnecki, Iain Dunning, Luke Marris, Guy Lever, Antonio Garcia Castañeda, Charles Beattie, Neil C. Rabinowitz, Ari S. Morcos, Avraham Ruderman, Nicolas Sonnerat, Tim Green, Louise Deason, Joel Z. Leibo, David Silver, Demis Hassabis, Koray Kavukcuoglu, Thore Graepel

**Year / Venue:** 2019 — *Science*, Vol. 364, Issue 6443, pp. 859–865

**arXiv:** [1807.01281](https://arxiv.org/abs/1807.01281) | **DOI:** [10.1126/science.aau6249](https://doi.org/10.1126/science.aau6249)

**Affiliation:** DeepMind

---

## Abstract

We used a tournament-style evaluation to demonstrate that an agent can achieve human-level performance in a three-dimensional multiplayer first-person video game, *Quake III Arena* in Capture the Flag mode, using only pixels and game points scored as input. We used a two-tier optimization process in which a population of independent RL agents are trained concurrently from thousands of parallel matches on randomly generated environments. Each agent learns its own internal reward signal and rich representation of the world.

---

## Introduction

CTF in Quake III Arena requires two teams to capture the opponent's flag while defending their own, demanding navigation, planning, collaboration, and real-time tactical adaptation. Successful play requires balancing cooperation with teammates and competition with opponents — all from raw visual inputs.

The key challenge is **sparse and delayed reward**: an agent may take thousands of actions before receiving a meaningful signal. The paper solves this via learned internal reward functions combined with population-based training, enabling self-organized effective learning curricula without hand-engineered intermediate rewards.

---

## Methods

### The FTW (For The Win) Agent

A novel **two-tier optimization process**:

#### Inner Optimization: Temporally Hierarchical RL

Each agent uses a hierarchical recurrent neural network with **two LSTMs at different timescales**:

- **Fast-timescale LSTM:** Updates at every environmental timestep; outputs a variational posterior over a latent variable used for policy, value function, and auxiliary task predictions
- **Slow-timescale LSTM:** Updates every τ timesteps (τ ∈ [5, 20)), outputting a latent prior at the slower timescale

An **external working memory module** (inspired by human episodic memory) complements the recurrent structure. Agents are trained with model-free RL optimizing learned internal rewards.

#### Outer Optimization: Population-Based Training (PBT)

A population of **P = 30** independent agents trained concurrently in thousands of parallel CTF matches on randomly generated maps. PBT evolves:
- Each agent's **internal reward transformation** (how game events are weighted)
- **Hyperparameters** (learning rate, loss weights, timescale τ)

At each evaluation interval, agents with win probability < 70% copy policy + internal reward + hyperparameters from a better-performing agent, then perturb the values by ±20%. This is a **meta-game** where the meta-reward is match victory — hence "For The Win."

**Training scale:** ~450,000 flag capturing games ≈ four years of human gameplay experience per agent.

---

## Key Results

### Human-Level and Superhuman Performance

Tournament-style evaluation with 40 human participants:
- FTW agents achieved **Elo ~1,600** vs. ~1,300 for strong humans and ~1,050 for average humans
- Humans rated FTW agents as **"more collaborative than human teammates"** in surveys

### Robustness to Reaction Time

With reaction times artificially slowed to 267ms (human average), agents still won **~79% of matchups** against strong humans — advantage comes from strategy, not reflexes.

### Exploitability Test

Two professional game testers played 12 hours continuously against a fixed FTW pair and could only win **25% of games**.

### Emergent Behaviors

Without explicit programming, agents developed:
- Base defense
- Opponent base camping
- Teammate following and escort
- Flag retrieval coordination

### Rich Internal Representations

Logistic regression on agent activations successfully predicted 200+ binary ground-truth game features (e.g., "Do I have the flag?", "Did I see my teammate recently?"), confirming agents learned high-level game knowledge.

---

## Conclusion

An artificial agent can achieve human-level performance in a complex 3D multiplayer FPS using only raw visual input and game score. Key principles:

1. **Multi-agent training as a natural curriculum:** Competing and cooperating with a diverse population drives robust, generalizable strategies
2. **Learned internal rewards solve sparse credit assignment:** Evolving dense reward signals enables effective RL with rare external rewards
3. **Temporal hierarchy enables multi-scale reasoning:** Separate fast and slow streams support reactive and strategic decision-making

These ideas have since influenced AlphaStar and other major AI achievements.

---

## Links

- **arXiv:** https://arxiv.org/abs/1807.01281
- **Science DOI:** https://doi.org/10.1126/science.aau6249
- **DeepMind blog:** https://deepmind.google/blog/capture-the-flag-the-emergence-of-complex-cooperative-agents/
