# Research Plan

**Emergent Cooperation and Collective Agency in CoGames**

## 1. Motivation

Multi-agent alignment problems are fundamentally about **how individual learning systems coordinate into higher-level collective intelligence**.

The Softmax inspiration list suggests a coherent direction:

- **Intrinsic altruism** (Wang et al., 2019)
- **Social influence rewards** (Jaques et al., 2019)
- **Reciprocity under uncertain social preferences** (Baker et al., 2020)
- **Population-based emergent teamwork** (Jaderberg et al., 2019)
- **Phase synchronization enabling higher-level agency** (Levin et al.)

The common hypothesis is:

> Collective intelligence emerges when agents develop internal motivations and interaction structures that allow them to synchronize behavior and form higher-level functional units.
> 

CoGames is an ideal experimental platform because it already supports:

- multi-agent PPO
- cooperative tasks
- agent role diversity
- controlled environments

The goal of this research program is **not merely to improve performance**, but to observe **qualitatively new cooperative behaviors and emergent coordination structures.**

---

# 2. Baseline Architecture

CoGames currently uses:

**Multi-agent PPO with centralized critic**

Properties:

Actor:

```
π_i(a | o_i)
```

Critic:

```
V(s)
```

Where:

- each agent observes `o_i`
- critic sees global state `s`
- shared critic stabilizes training
- policies are typically shared or identical across agents

This corresponds to the **Centralized Training, Decentralized Execution (CTDE)** paradigm.

---

# 3. Capture-the-Flag Comparison

DeepMind’s **Capture-the-Flag agent (FTW)** introduced several relevant ideas.

Key architectural elements:

### 1. Population-based training (PBT)

30 agents trained simultaneously.

Agents play with and against each other.

Population evolves:

- hyperparameters
- intrinsic reward weights

### 2. Decentralized policies

Each agent learns independently from its own observations.

### 3. Learned internal reward

Agents transform game events into dense rewards that approximate winning.

### 4. Multi-timescale recurrent architecture

Hierarchical temporal representations enable long-horizon coordination.

---

### Centralized vs Decentralized Critics

| Approach | Strength | Weakness |
| --- | --- | --- |
| Centralized critic | stable gradients | may suppress specialization |
| Decentralized critic | emergent roles | training instability |

Thus **one research axis** is evaluating which is better for CoGames.

---

# 4. Experimental Program

## Experiment 1 — Baseline CoGames

Goal: establish performance baseline.

Setup:

- standard MAPPO
- centralized critic
- shared policy

Metrics:

- episode reward
- team reward
- cooperation metrics (resource sharing, assist actions)
- training stability

---

## Experiment 2 — Decentralized Critics

Motivation:

In Capture-the-Flag, agents developed specialized behaviors partly because learning was decentralized.

Setup:

- independent critics per agent
- policies may still share parameters

Critic:

```
V_i(o_i)
```

Hypothesis:

- decentralized critics encourage role specialization
- coordination emerges from interaction rather than shared value estimation

Metrics:

- role differentiation
- coordination latency
- win-rate improvements

---

## Experiment 3 — Population-Based Training

Inspired by **FTW architecture**.

Instead of training **one policy**, train **a population**.

Example:

Population = 16 policies.

Training loop:

```
for generation:
    run games between policies
    evaluate policy fitness
    copy weights from top performers
    mutate hyperparameters
```

Mutations may include:

- learning rate
- entropy coefficient
- reward weights
- exploration noise

This introduces **evolutionary exploration** alongside gradient learning.

Hypothesis:

Population diversity enables discovery of:

- complementary strategies
- cooperative roles
- adaptive tactics

---

## Experiment 4 — Intrinsic Altruism

Based on:

**Evolving Intrinsic Motivations for Altruistic Behavior**

Architecture modification:

Agents learn an **intrinsic reward network**

Total reward:

```
R_total = R_env + R_intrinsic
```

Intrinsic reward network input features:

- teammate rewards
- teammate states
- cooperative events

Example:

```
R_intrinsic = f(
    teammate_reward,
    shared_resource_state,
    teammate_distance
)
```

Evolution or population selection can tune the reward network parameters.

Hypothesis:

Agents will learn **pro-social behaviors** such as:

- resource preservation
- assisting teammates
- avoiding selfish actions

---

## Experiment 5 — Social Influence Reward

Based on:

**Social Influence as Intrinsic Motivation**

Agents are rewarded when their actions **change the behavior of others**.

Influence metric:

```
I(a_i) = KL(
    P(a_j | state, with agent i action)
    ||
    P(a_j | state, without agent i action)
)
```

If an action causes teammates to change behavior, influence increases.

Agents receive intrinsic reward:

```
R_influence = β * influence_score
```

Hypothesis:

Agents will actively **coordinate behavior**, not just optimize local reward.

This may produce:

- signaling behavior
- leadership roles
- coordination strategies

---

## Experiment 6 — Randomized Social Preferences

Based on:

**Emergent Reciprocity and Team Formation**

During training, reward matrix changes per episode.

Example:

True reward matrix:

```
T =
[1.0 0.0 0.0]
[0.2 0.8 0.0]
[0.1 0.1 0.8]
```

Each agent optimizes:

```
R_i = Σ_j T_ij * r_j
```

But agents observe only a **noisy estimate** of T.

Result:

Agents must infer:

- who benefits from cooperation
- who reciprocates
- who defects

Hypothesis:

Agents will develop:

- reciprocity strategies
- coalition formation
- reputation mechanisms

---

## Experiment 7 — Synchronization and Collective Agency

Inspired by:

**Phase Synchronization and Higher-Level Agency**

Key idea:

Higher-level systems emerge when components synchronize behavior.

Implementation ideas:

### Temporal synchronization reward

Encourage agents to align action timing.

Example metric:

```
sync = correlation(action_i, action_j)
```

Reward for high synchronization.

### Shared latent representation

Agents share a communication vector.

```
h_team = mean(h_i)
```

Policies condition on:

```
π_i(a | o_i, h_team)
```

Hypothesis:

Agents may evolve **collective behaviors** resembling:

- flocking
- coordinated attack/defense
- synchronized resource usage

---

# 5. Metrics

Beyond reward, we measure **collective intelligence indicators**.

### Behavioral metrics

- cooperation frequency
- assist actions
- resource fairness
- role specialization

### Population metrics

- policy diversity
- strategy clusters
- coalition stability

### Collective agency metrics

- coordination entropy
- synchronization index
- mutual information between agents

---

# 6. Expected Outcomes

Possible emergent behaviors:

- specialization (scout, defender, collector)
- coalition formation
- signaling protocols
- resource governance
- synchronized group actions

The most interesting result would be the appearance of **stable cooperative structures not explicitly programmed**.

---

# 7. Long-Term Research Direction

This program moves toward a broader question:

> How do independent learning systems transition into higher-level cooperative agents?
> 

CoGames can become a **testbed for emergent collective intelligence**.

Potential future directions:

- evolving communication protocols
- hierarchical multi-agent organizations
- open-ended multi-agent ecosystems
