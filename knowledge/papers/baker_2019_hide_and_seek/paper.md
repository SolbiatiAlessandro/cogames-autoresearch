# Emergent Tool Use from Multi-Agent Autocurricula

**Authors:** Bowen Baker, Ingmar Kanitscheider, Todor Markov, Yi Wu, Glenn Powell, Bob McGrew, Igor Mordatch

**Year / Venue:** 2019 (arXiv preprint); published at ICLR 2020

**arXiv ID:** [1909.07528](https://arxiv.org/abs/1909.07528)

**Affiliation:** OpenAI

---

## Abstract

We study how competitive multi-agent dynamics can induce emergent behavior in physically grounded environments. Agents are trained in a simple hide-and-seek game using standard reinforcement learning at scale, with no explicit incentive to interact with objects in the environment. Despite this, agents autonomously discover six distinct strategic phases — including tool use, object manipulation, and multi-agent coordination — each creating new competitive pressure that drives the next round of adaptation. The authors term this process an *autocurriculum*: a self-supervised curriculum emerging from agent competition rather than external task specification. They further show that agents pre-trained in this environment transfer useful representations to downstream intelligence tests, outperforming intrinsic motivation baselines on several tasks. Results suggest that multi-agent competition scales better with environmental complexity than directed exploration methods and produces behaviors more aligned with human-relevant skills.

---

## Introduction

A central challenge in AI is building agents capable of solving a wide range of complex, human-relevant tasks without exhaustive manual specification of rewards or demonstrations. Prior work with multi-agent self-play (e.g., AlphaGo, OpenAI Five, AlphaStar) has shown that competitive dynamics can produce sophisticated strategies in abstract, bounded domains. This paper extends that line of work to physically grounded environments, asking whether competitive pressure alone can drive open-ended skill acquisition — including the spontaneous emergence of tool use.

The motivation draws from evolutionary biology: competition and co-evolution on Earth have continuously driven increases in behavioral complexity. The authors hypothesize that analogous competitive dynamics in simulation can create *implicit autocurricula*, where each new strategy discovered by one team pressures the opposing team to adapt, generating an ongoing, compounding sequence of skill development.

Critically, the hide-and-seek setup gives agents **no explicit incentive** to interact with any objects in the environment. All tool use and environmental manipulation emerges purely from competitive pressure — agents discover the instrumental value of objects because manipulating them confers a competitive advantage.

---

## Methods

### Environment: Hide-and-Seek

The game is played in a physics-based simulation (MuJoCo engine) on an 18-meter square arena with randomly generated immovable walls and rooms. Two teams compete:

- **Hiders** receive a reward of +1 when fully hidden from all seekers, −1 when spotted.
- **Seekers** receive the inverse reward.
- A **preparation phase** occupies 40% of each 240-timestep episode, during which seekers are immobilized and hiders may prepare.

Each episode contains:
- 1–3 agents per team
- 3–9 movable boxes of various shapes
- 2 movable ramps
- Randomly generated immovable room structures

**Object locking** is a key mechanic: any agent can lock or unlock an object, but only a team member from the team that originally locked an object can unlock it. This forces team coordination and strategic use of the locking action.

### Agent Architecture

Agents use **entity-centric observations** processed through a **masked residual self-attention** mechanism. Each entity type (agents, boxes, ramps) shares learned embedding weights. The self-attention layer handles variable numbers of entities while maintaining permutation invariance. Entities not visible to an agent are masked during attention, enabling partial observability.

This architecture supports decentralized execution: each agent acts using only its own observations at test time, while training uses **omniscient value functions** (which access global state). Centralized value functions were critical to achieving higher-order emergent behaviors.

### Training

- **Algorithm:** Proximal Policy Optimization (PPO) with Generalized Advantage Estimation (GAE)
- **Distributed framework:** OpenAI's *Rapid* large-scale RL infrastructure
- **Policy parameters:** Shared across teammates
- **Scale:** ~132.3 million episodes (31.7 billion frames) over 34 hours to reach stage 4

---

## Key Results

### Six Emergent Strategic Phases

| Phase | ~Episodes Required | Description |
|---|---|---|
| 1. Running & Chasing | ~25M | Basic pursuit and evasion |
| 2. Fort Building | ~100M | Hiders construct multi-box shelters |
| 3. Ramp Use | ~175M | Seekers use ramps to bypass shelters |
| 4. Ramp Defense | ~185M | Hiders relocate and lock ramps away |
| 5. Box Surfing | ~380M | Seekers ride locked boxes into forts |
| 6. Surf Defense | End of training | Hiders preemptively lock all unused boxes |

No explicit incentives for object interaction were provided — all tool use arose purely from competitive dynamics.

### Multi-Agent Competition vs. Intrinsic Motivation

Multi-agent competition outperformed count-based intrinsic motivation and Random Network Distillation (RND) baselines in both emergent behavior complexity and downstream transfer tasks.

### Transfer Learning

Hide-and-seek pre-trained agents outperformed baselines on 3 of 5 intelligence probe tasks (object permanence, navigation, memory), demonstrating generalizable skills.

### Team Coordination

Larger teams locked **36% more objects** than single agents, demonstrating emergent cooperative behavior without explicit cooperation rewards.

---

## Conclusion

This paper demonstrates that competitive multi-agent interactions in a physically grounded hide-and-seek environment are sufficient to produce six distinct phases of emergent behavior — including sophisticated tool use, object manipulation, and team coordination — without any explicit incentives to engage with objects. The **multi-agent autocurriculum** concept establishes that competitive pressure can serve as a scalable, open-ended training signal.

Key conclusions:
1. Multi-agent competition can serve as a scalable open-ended training signal
2. Physically grounded environments with competitive dynamics are a promising substrate for emergent tool use
3. A transfer learning framework provides a principled way to evaluate open-ended training
4. Multi-agent autocurricula scale better with environmental complexity than intrinsic motivation

---

## Links

- **arXiv:** https://arxiv.org/abs/1909.07528
- **OpenAI Blog:** https://openai.com/research/emergent-tool-use
