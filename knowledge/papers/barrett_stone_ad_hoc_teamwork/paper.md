# Ad Hoc Teamwork / Zero-Shot Coordination (Barrett & Stone)

This folder covers the foundational ad hoc teamwork challenge paper and its key follow-on algorithmic work (PLASTIC).

---

## Part 1: The Foundational Challenge Paper

**Full Title:** Ad Hoc Autonomous Agent Teams: Collaboration without Pre-Coordination

**Authors:** Peter Stone, Gal A. Kaminka, Sarit Kraus, Jeffrey S. Rosenschein

**Venue:** AAAI 2010 (Atlanta, Georgia)

**DOI:** [10.1609/aaai.v24i1.7529](https://doi.org/10.1609/aaai.v24i1.7529)

**PDF:** https://cdn.aaai.org/ojs/7529/7529-13-11059-1-2-20201228.pdf

---

### Abstract

As autonomous agents proliferate in the real world, they will increasingly need to band together for cooperative activities with previously unfamiliar teammates. In such **ad hoc team settings**, team strategies cannot be developed a priori. Rather, an agent must be prepared to cooperate with many types of teammates: it must collaborate without pre-coordination.

This paper challenges the AI community to develop theory and implement prototypes of ad hoc team agents. It defines the concept, specifies an evaluation paradigm, and provides examples of theoretical and empirical approaches.

---

### Introduction

Historically, autonomous agents were deployed within cohesive development groups that could pre-tune and coordinate their behaviors. As agents are deployed longer and the number of organizations building them grows, they increasingly encounter teammates they were not designed to work with and who don't share the same communication protocols, world models, or sensing/acting capabilities.

The key recursive complexity: a well-designed ad hoc agent must not only model its teammates but be aware that its teammates may simultaneously be modeling it — creating a mutually adaptive, recursive modeling situation.

---

### Methods

#### Theoretical Approach: Finite-Horizon Cooperative k-Armed Bandit

Stone and Kraus instantiate a restricted version as a **finite-horizon cooperative k-armed bandit**:
- The ad hoc agent selects which "arm" to pull at each step, corresponding to which action to take alongside a fixed-behavior teammate
- Goal: maximize cumulative reward over a finite horizon
- Key contribution: **polynomial dynamic programming algorithm** computing the optimal action when arm payoffs are drawn from a discrete distribution

#### Empirical Approach: Teammate Modeling

For complex realistic settings, the paper proposes:
- Observe teammate behaviors and infer their policies or types
- Select own actions to best complement inferred teammate behaviors
- Evaluate across a distribution of possible teammates

#### Evaluation Paradigm

An ad hoc agent is assessed by expected team performance across a **distribution of possible teammate types** and task variants — emphasizing robustness and generality rather than performance against a single fixed partner.

---

### Key Contributions

1. **Formal definition** of ad hoc teamwork as a distinct research problem in multiagent systems
2. **Evaluation framework** for measuring ad hoc agent performance across diverse teammate distributions
3. **Theoretical result:** the finite-horizon cooperative k-armed bandit is solvable in polynomial time
4. **Key research dimensions** for decomposing the challenge:
   - Knowledge about the environment
   - Knowledge about teammates (prior, partial, or none)
   - Communication capabilities
   - Team size and heterogeneity
   - Task complexity

---

## Part 2: The Key Algorithmic Follow-On — PLASTIC

**Full Title:** Making Friends on the Fly: Cooperating with New Teammates

**Authors:** Samuel Barrett, Avi Rosenfeld, Sarit Kraus, Peter Stone

**Venue:** *Artificial Intelligence*, vol. 242, pp. 132–171, 2017

**Semantic Scholar:** https://www.semanticscholar.org/paper/Making-friends-on-the-fly:-Cooperating-with-new-Barrett-Rosenfeld/ddec0eb2a9cc96aabea036ff42a19df5ab518875

---

### Abstract

This work introduces **PLASTIC** — a general-purpose ad hoc teamwork algorithm that reuses knowledge learned from previous teammates or provided by experts to quickly adapt to new teammates without pre-coordination.

---

### Methods: The PLASTIC Algorithm

**PLASTIC-Model:** Builds probabilistic behavioral models of previous teammate types and uses online planning against these models.
- At each timestep: Bayesian belief update over the discrete space of known teammate types, using observed actions as evidence
- Selects best action under current teammate type distribution

**PLASTIC-Policy:** Learns separate cooperative policies for each known teammate type, then performs online selection among these policies using Bayesian belief updates.

**TwoStageTransfer:** A novel transfer learning algorithm enabling PLASTIC to leverage partial similarity between past and new teammates, outperforming existing transfer learning baselines.

---

### Evaluation

Evaluated on two benchmark domains:
- **Pursuit (predator-prey) domain:** tested against 40+ unknown teams created by independent developers
- **RoboCup 2D half-field offense (HFO):** tested against 7 previously unknown teams in complex continuous-action soccer simulation

---

### Key Results

- PLASTIC successfully identified and exploited behavioral similarities between past and new teammates
- Both PLASTIC-Model and PLASTIC-Policy achieved strong adaptation performance
- TwoStageTransfer outperformed existing transfer learning approaches
- Extended effectively to continuous state/action spaces and unknown number of teammate types

### Three Dimensions of Ad Hoc Teamwork

The paper identifies three organizing dimensions:
1. The degree to which teammates are known in advance
2. The variety and complexity of tasks
3. The speed of required adaptation

---

## Summary of the Research Line

| Paper | Venue | Year | Key Contribution |
|---|---|---|---|
| Ad Hoc Autonomous Agent Teams (Stone et al.) | AAAI | 2010 | Problem definition, evaluation framework, k-armed bandit theory |
| Empirical Evaluation in Pursuit Domain (Barrett et al.) | AAMAS | 2011 | First empirical ad hoc teamwork study |
| Teamwork with Limited Knowledge (Barrett et al.) | AAAI | 2013 | Testing against 40+ external unknown teams |
| Making Friends on the Fly / PLASTIC (Barrett et al.) | *Artificial Intelligence* | 2017 | PLASTIC algorithm, Bayesian teammate modeling, TwoStageTransfer |

---

## Links

- **Foundational 2010 paper (AAAI):** https://ojs.aaai.org/index.php/AAAI/article/view/7529
- **PLASTIC paper (Semantic Scholar):** https://www.semanticscholar.org/paper/Making-friends-on-the-fly:-Cooperating-with-new-Barrett-Rosenfeld/ddec0eb2a9cc96aabea036ff42a19df5ab518875
- **Survey of Ad Hoc Teamwork Research (arXiv):** https://arxiv.org/abs/2202.10450
- **Peter Stone's page:** https://www.cs.utexas.edu/~pstone/Papers/bib2html/b2hd-AAAI10-adhoc.html
