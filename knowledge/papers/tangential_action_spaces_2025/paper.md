# Tangential Action Spaces: Geometry, Memory and Cost in Holonomic and Nonholonomic Agents

**Author:** Marcel Blattner

**Year:** 2025

**Venue:** arXiv preprint; submitted September 2, 2025

**Field:** Systems and Control / Embodied Cognition / Multi-Agent Systems

**arXiv:** [2509.03399](https://arxiv.org/abs/2509.03399)

---

## Abstract

This paper introduces **Tangential Action Spaces (TAS)**, a geometric framework that models embodied agents as hierarchies of manifolds linked by projection maps — from physical states to cognitive representations, and onward to intentional goals. Lifting intentions back to physical actions can proceed along multiple routes, which generally differ in energy cost and in whether they leave memory-like (path-dependent) traces.

Three core results are established:

1. When the physical-to-cognitive projection is **locally invertible**, there is a unique lift that minimises instantaneous energy and produces no path-dependent memory; any lift that induces memory entails strictly positive excess energy.
2. When multiple physical states map to the same cognitive state (**fibration**), the energy-minimising lift is the weighted pseudoinverse determined by the physical metric.
3. In systems with **holonomy**, excess energy grows quadratically with the size of the induced memory for sufficiently small loops.

---

## Introduction

TAS addresses a long-standing gap in motor control and embodied cognition: the lack of a unified mathematical language that simultaneously accounts for physical embodiment, cognitive abstraction, energetic efficiency, and path-dependent memory.

The framework is built around three nested manifolds:

- **Physical space (P):** Complete bodily states — muscle activations, joint angles, proprioception, neural dynamics.
- **Cognitive space (C):** Task-relevant representations — hand position, grip aperture, learned motor schemas.
- **Intentional space (I):** Goal states representing desired outcomes.

Projection maps Φ: P → C and Ψ: C → I implement successive abstraction layers. The critical operation is the **lift** — reversing abstraction to translate an intentional change into a physical action. Lifts are not unique: multiple physical paths can achieve the same cognitive outcome, differing in energy cost and path-dependent "memory" (holonomy).

---

## Methods

### Core Mathematical Structure

A TAS consists of surjective submersions linking three smooth manifolds with dimensions satisfying m ≥ n ≥ k (physical ≥ cognitive ≥ intentional). Two primary geometric cases:

- **Diffeomorphisms (m = n):** Locally invertible projections, yielding a unique geometric lift.
- **Fibrations (m > n):** Multiple physical states map to the same cognitive state, creating a family of valid lifts.

### The Three Main Results

**Result 1 — Geometric Lift (Diffeomorphisms):**
When Φ is locally invertible, the unique energy-optimal lift is:
```
L_geom = DΦ^{-1} Δc
```
This lift produces zero holonomy: closed loops in cognitive space always close in physical space.

**Result 2 — Metric Lift (Fibrations):**
For fibrations, the energy-minimising lift is the metric-weighted pseudoinverse:
```
L_metric = G^{-1} DΦ^T [DΦ G^{-1} DΦ^T]^{-1} Δc
```

**Result 3 — Cost-Memory Duality (Theorem 1):**
Any path-dependent behaviour requires excess energy proportional to `||v_vert||^2_G`. For small loops of area A, excess effort scales quadratically as `κ||Δu_vert||^2 + o(A^2)`.

### Classification of Embodied Systems

| Class | Description |
|---|---|
| Intrinsically Conservative | Diffeomorphisms with geometric lifts; zero holonomy, minimal cost |
| Conditionally Conservative | Fibrations with flat connections; zero holonomy for contractible loops |
| Geometrically Nonconservative | Fibrations with curved connections; holonomy from curvature |
| Dynamically Nonconservative | Diffeomorphisms with prescribed lifts; engineered path dependence |

### Reflective TAS (rTAS)

An extension adds a learnable **model manifold M** alongside physical states. A block metric formalises an effort-learning trade-off, allowing simultaneous optimisation of physical action and belief updating. Multi-agent simulations of coupled agents exhibit role asymmetries and cooperative behaviours emerging from coupled reflective metrics.

---

## Key Results

1. **Cost-Memory Duality:** Path-dependent behaviour is not free — it requires excess energy proportional to the square of the induced memory (holonomy). This is the central theorem.

2. **Metric Lift as the Energetic Optimum:** In fibrated systems, the energy-minimising action is the metric-weighted pseudoinverse.

3. **Fourfold Classification:** Organises a wide range of embodied agents under one geometric framework.

4. **Two-Agent Simulations:** rTAS simulations exhibit role asymmetries, policy-induced phase transitions in cooperation-pursuit dynamics, and formation control from coupled reflective metrics.

5. **Design Principles for Robotics:**
   - Metric-lift controllers minimise instantaneous energy but encode no learning
   - Deliberately chosen vertical components enable memory encoding at controlled energetic cost
   - Curved bundle connections create geometric memory without explicit control rules

6. **Testable Biological Predictions:** Biological systems should show quadratic scaling of path-dependent memory costs; repeated trajectories should become cheaper through learning of flat connections.

---

## Conclusion

Tangential Action Spaces provides a mathematically rigorous, unified framework for understanding the interplay of embodiment, memory, and energetic efficiency in both biological and artificial agents. The central result — that path-dependent behaviour necessarily incurs excess energy — explains the diversity of biological motor strategies. Multi-agent extensions via rTAS demonstrate that the framework scales to coupled agents, producing emergent cooperative and role-asymmetric behaviours from first principles of differential geometry.

**Relevance to cooperative MARL:** The rTAS extension directly addresses two-agent cooperative settings and provides a geometric formalism for understanding how cooperation emerges from the interaction of embodied agents with different action manifold structures.

---

## Links

- **arXiv:** https://arxiv.org/abs/2509.03399
- **HTML version:** https://arxiv.org/html/2509.03399
