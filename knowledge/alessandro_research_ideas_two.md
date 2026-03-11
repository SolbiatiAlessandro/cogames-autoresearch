# CoGames Research Plan

*Multi-Agent Coordination via Emergent Alignment — Alessandro Solbiati, March 2026*

---

## Background & Context

CoGames (CogsGuard) is a multi-agent coordination game where teams of Cogs compete to control junctions on a grid map. This research plan explores how emergent alignment principles — phase synchronization, causal influence, and causal emergence — can bootstrap cooperation in MAPPO-trained agents without hard-coded milestones.

---

## Current State of Training

Architecture: CNN+LSTM actor-critic, 2.5M params, MAPPO with parameter sharing (PufferLib/PPO).

Training results after 2M steps (miner_tutorial):

- Agent learned to move (move.success: 7 → 479) but completely stalled
- clipfrac and approx_kl collapsed to 0 — policy stopped updating
- explained_variance degraded (0.46 → 0.38) — critic got worse
- deposit_diversity stayed at 0 — agent never deposited resources

Root cause: base junction-control reward is too sparse. 2M steps is significantly undercooked vs SMAC benchmarks (10-50M steps for comparable tasks).

---

## Key Papers & Theoretical Grounding

**Coordination & Alignment**

- Social Influence as Intrinsic Motivation (Jaques et al., ICML 2019, MIT) — agents rewarded for causal influence on teammates via Convergence Cross Mapping; bootstraps cooperation without explicit team rewards
- QMIX (Rashid et al., ICML 2020) — value decomposition into individual agent values with mixer network; implicit coordination through value factorization
- MAPPO (Yu et al., 2021) — centralized critic sees global state during training; simpler than QMIX but strong on SMAC leaderboard
- Zero-Shot Coordination / Ad Hoc Teamwork (Barrett & Stone) — agents learning policies that generalize to unseen teammates

**Emergent Complexity**

- Causal Emergence 2.0 (Hoel, 2025) — team-level causal power can exceed sum of parts
- Phase Synchronization & Agency — phase sync drives transitions to higher levels of agency; synchronization metrics as intrinsic motivation
- Tangential Action Spaces (TAS) — geometric formalism making cooperative moves computationally cheaper
- MACIE (2024) — Synergy Index quantifies emergence in cooperative MARL tasks

**Open-Ended Learning**

- Hide-and-Seek (Baker et al., OpenAI 2019) — emergent tool use and strategy from self-play against diverse opponents
- Enhanced POET / AGRec — agents generate their own curriculum dynamically without hard-coded milestones

---

## Theoretical Thread: Emergent Alignment

Agents start uncoordinated (high entropy, low phase sync) → intrinsic motivation pulls them toward synchronized behavior → which increases causal emergence at team level → meaning the team gains causal power over the environment that individual agents couldn't have alone → action space geometry makes this synchronized state computationally cheaper to reach.

Key insight: instead of hard-coding milestones like "deposit every N steps," agents discover synchronization points through intrinsic motivation. Biological analog: cells don't need programmed instructions to form organs — coordination emerges from local incentives.

---

## Series of Experiments

**Experiment 1: Baseline — Dense Rewards + Scale**
Goal: establish whether sparse reward + low step count are the only blockers.

- Stack credit + milestones reward variants (already in reward_variants.py)
- Scale to 10-20M steps
- Monitor: miner.gained, deposit_diversity, explained_variance
- Expected: agents learn miner role; coordination still absent

**Experiment 2: MAPPO vs QMIX on CoGames**
Goal: test whether value decomposition helps when coordination is the bottleneck.

- Implement QMIX mixer network on top of existing agent value functions
- Compare MAPPO vs QMIX on miner_tutorial with dense rewards
- Hypothesis: QMIX may outperform MAPPO in CoGames because junction control requires genuine team interdependence, unlike SMAC's individual unit combat

**Experiment 3: Social Influence as Intrinsic Reward**
Goal: bootstrap coordination without explicit team rewards using causal influence.

- Implement influence reward: train predictor model to predict agent B's next action from agent A's recent history
- Add influence bonus to individual agent reward alongside task reward
- Measure: do agents develop emergent coordination patterns (taking turns, role specialization)?
- Reference: Jaques et al. ICML 2019

**Experiment 4: Phase Synchronization as Intrinsic Motivation**
Goal: test whether behavioral synchrony naturally produces emergent coordination milestones.

- Implement phase sync metric: measure Jensen-Shannon divergence between agents' action distributions across team
- Add phase sync bonus to reward — agents rewarded when team behavioral distributions converge
- Key test: do agents self-organize temporal structure without it being hard-coded?
- Compare: does this discover the same milestones as hand-coded credit + milestones variants?

**Experiment 5: Causal Emergence as Meta-Reward**
Goal: use MACIE Synergy Index as auxiliary reward to encourage team-level causal power.

- Instrument training with Synergy Index measurement
- Add emergence bonus when Synergy Index exceeds threshold
- Hypothesis: creates pressure for agents to form cohesive team structures rather than independent play

**Experiment 6: Heterogeneous Opponents + Zero-Shot Coordination**
Goal: train policies robust to unseen teammates (key Softmax requirement).

- Train against mixed teams: scripted + trained agents
- Evaluate zero-shot coordination: does trained policy work with completely unseen partner policies?
- Optional: Population-Based Training (PBT) — maintain diverse population, cull weak agents, mutate strong ones

---

## Proposed Architecture (Three-Layer Reward)

- Layer 1 — Dense task rewards (existing): credit + milestones variants, role shaping
- Layer 2 — Social coordination rewards (new): causal influence bonus + phase sync bonus as auxiliary intrinsic motivation
- Layer 3 — Emergence meta-reward (experimental): Synergy Index as team-level auxiliary objective

No privileged causation — each layer has independent causal input; no layer overrides another.

---

## Practical Notes

- Wall-clock estimate: ~3-7 days per run on decent GPU for 20M steps
- SMAC bottleneck is simulation speed, not GPU compute — same likely applies to CoGames
- Network size (2.5M params) is fine — don't increase unless task complexity demands it
- Start simple: Experiment 1 first, collect real data before adding complexity
- MAPPO dominates SMAC leaderboard — world models like Dreamer not competitive on symbolic token observations

---

## Key References

- Jaques et al. (2019) — Social Influence as Intrinsic Motivation for MARL, MIT Media Lab, ICML 2019
- Yu et al. (2021) — MAPPO paper
- Yuan et al. (2022) — Is Independent Learning All You Need in SMAC?
- Rashid et al. (2020) — QMIX, ICML 2020
- Baker et al. (2019) — Emergent Tool Use from Multi-Agent Interaction, OpenAI hide-and-seek
- Hoel (2025) — Causal Emergence 2.0
- Levin (2022) — Technological Approach to Mind Everywhere
- Noble (2012) — Theory of Biological Relativity
- MACIE (2024) — Multi-Agent Causal Intelligence Explainer
- Phase Sync paper — An Ability to Respond Begins with Inner Alignment
- Tangential Action Spaces (2025)
