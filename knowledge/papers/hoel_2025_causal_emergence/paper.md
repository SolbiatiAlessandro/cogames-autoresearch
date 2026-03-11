# Causal Emergence 2.0: Quantifying Emergent Complexity

**Authors:** Erik Hoel & Abel Jansma

**Year / Venue:** 2025 (preprint); arXiv:2503.13395 [cs.IT]

**Submitted:** March 17, 2025 (latest revision: April 21, 2025)

**Link:** https://arxiv.org/abs/2503.13395

---

## Abstract

Complex systems can be described at myriad different scales, with multiscale causal structure (e.g., a computer described at the microscale of hardware circuitry, the mesoscale of machine code, and the macroscale of the operating system). While scientists study systems across the full hierarchy of scales — from microphysics to macroeconomics — there is longstanding debate about what macroscales can add beyond mere compression.

To resolve this, the paper introduces a new theory of emergence in which the different scales of a system are treated as **slices of a higher-dimensional object**. The theory can distinguish which scales possess unique causal contributions and which are not causally relevant. It is constructed from an axiomatic notion of causation, demonstrated in coarse-grains of Markov chains. The result is a novel complexity measure quantifying how widely distributed a system's causal workings are across its hierarchy of scales — called **emergent complexity**.

---

## Introduction

Erik Hoel's original 2013 causal emergence theory (CE 1.0) offered a mathematical framework treating emergence as a common phenomenon. The core insight: causal relationships at the macroscale have an innate advantage over the microscale — they are less affected by noise and uncertainty. Conditional probabilities can be much stronger between macro-variables than micro-variables even when the two levels describe the very same underlying system.

CE 1.0 was limited: it identified a single optimal macroscale, neglecting the rich **multiscale structure** found in real complex systems such as brains, economies, or software stacks. CE 2.0 addresses this directly by asking not "is there an emergent macroscale?" but "how is causal contribution distributed across all scales?"

---

## Key Framework

### Causal Primitives (Axiomatic Foundation)

CE 2.0 is grounded in two fundamental causal primitives:

- **Sufficiency** — P(effect | cause): How reliably a cause brings about its effect (operationalized as *determinism*).
- **Necessity** — 1 − P(effect | set of causes, ¬cause): How uniquely a cause is responsible for an effect (operationalized as *specificity*).

### The Causal Path and Apportioning Schema

Rather than searching for a single best scale, CE 2.0 defines a **micro→macro path**: an ordered sequence of valid coarse-grainings from the finest microscale to the coarsest macroscale. At each step:
- Changes in causal primitives (ΔCP) are calculated
- Each scale's **unique causal contribution** is apportioned (no double-counting)
- All macroscales must satisfy **dynamical consistency**

### Emergent Complexity (EC)

The central new metric:

```
EC = − Σ (p_i · log₂(p_i))
```

where p_i represents the normalized causal contribution at each step along the micro→macro path.

- **Low EC ("top-heavy"):** Causal contribution concentrated at one or a few scales
- **High EC ("scale-free"):** Causal contribution evenly distributed across many scales — maximal emergent complexity
- **"Bottom-heavy":** Causal contribution concentrated at the microscale — little emergence

### Engineering Emergence

A major result: systems can be deliberately **designed** with specific hierarchical causal structures:
- **"Balloon" configuration:** A single strongly emergent macroscale
- **Scale-free / maximally complex:** Causal contribution spread evenly across the full hierarchy

---

## Key Results

1. **Cost-Memory Duality:** Path-dependent behaviour requires excess energy above the geometric minimum
2. **CE 1.0 Superiority:** CE 2.0 correctly identifies macroscale causation in block models where CE 1.0 fails
3. **Causal Exclusion Resolution:** Multiple scales can simultaneously possess distinct causal relevance without contradiction
4. **Engineering Emergence:** Demonstrated constructively that emergence can be engineered by design

### Comparison to CE 1.0

In a block model example: when two equivalency classes have strong internal self-loops, CE 1.0 detects no macroscale causation, while CE 2.0 correctly recognizes significant macroscale causal contribution. CE 1.0's effective information depends on a size term (number of states) that can mask real macroscale causation; CE 2.0 bypasses this artifact.

---

## Conclusion

CE 2.0 represents a significant expansion and revision of the original causal emergence framework:

1. A fully axiomatic, multi-scale framework grounded in necessity and sufficiency
2. The **emergent complexity (EC)** metric quantifying how widely a system's causal workings are distributed across its scale hierarchy
3. Robustness to different interventional assumptions, overcoming a major criticism of CE 1.0
4. Constructive result showing emergence can be **engineered** by design
5. A principled resolution to the causal exclusion problem

Broad potential applications: physics, biology, neuroscience, economics, and especially **AI interpretability** — CE 2.0 could help characterize the multiscale causal structure of deep neural networks.

---

## Links

- **arXiv:** https://arxiv.org/abs/2503.13395
- **HTML version:** https://arxiv.org/html/2503.13395v3
- **Erik Hoel's introduction:** https://www.theintrinsicperspective.com/p/i-figured-out-how-to-engineer-emergence
