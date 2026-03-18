# Reward Component Analysis - Why Does Performance Degrade?

## Score Comparison
- **10-min run:** 73.2
- **30-min run:** 58.6
- **Difference:** -14.6 (20% worse)

## Detailed Metrics Breakdown

### Junction Control (Core Objective)
| Metric | 10-min | 30-min | Change | Analysis |
|--------|--------|--------|--------|----------|
| **Clips junctions held** | 1,197,292 | 1,199,203 | +1,911 ✅ | Slightly better |
| **Cogs junctions held** | 0.0 | 162.8 | +162.8 ⚠️ | Enemy gained control |
| **Aligned by agent** | 0.0 | 0.1 | +0.1 | Minimal improvement |

**Finding:** 30-min run allowed enemies (Cogs) to capture junctions. This is BAD in the mission objective.

### Resource Management
| Metric | 10-min | 30-min | Change | Analysis |
|--------|--------|--------|--------|----------|
| **Heart amount** | 1.6 | 1.5 | -0.1 | Slightly worse |
| **Carbon amount** | 8.0 | 5.2 | -2.8 ⬇️ | Less resources |
| **Carbon deposited** | 0.0 | 5.0 | +5.0 | Deposited more |

**Finding:** 30-min run has less carbon held but deposited more. Net resource state is worse.

### Agent Behavior
| Metric | 10-min | 30-min | Change | Analysis |
|--------|--------|--------|--------|----------|
| **Cells visited** | 2,523,870 | 2,211,889 | -311,981 ⬇️ | Less exploration |
| **Deaths** | 2.8 | 1.8 | -1.0 ✅ | Survived better |
| **Move success** | 4,723 | 4,708 | -15 | Slightly worse |
| **Move failed** | 3,344 | 3,373 | +29 | More failed moves |

**Finding:** 30-min policy is MORE CONSERVATIVE - explores less, dies less, but also less effective at objective.

## What's Actually Happening?

### 10-Min Policy (Score 73.2) ✅
**Behavior:**
- Aggressive exploration (2.5M cells visited)
- Maintains clips junction control (1.2M)
- Prevents enemy from gaining junctions (0 cogs held)
- Dies occasionally (2.8 deaths) but accomplishes objective
- High carbon reserves (8.0)

**Strategy:** Risk-taking, objective-focused

### 30-Min Policy (Score 58.6) ⬇️
**Behavior:**
- Conservative exploration (2.2M cells, 12% less)
- Still holds clips junctions BUT
- **Allows enemies to capture 162 junctions** 🚨
- Plays it safe (1.8 deaths vs 2.8)
- Burns through carbon faster (5.2 vs 8.0)

**Strategy:** Safety-first, loses sight of objective

## The Core Problem: Policy Drift Toward Suboptimal Safety

The policy learned to optimize for:
1. ✅ Not dying (deaths 2.8 → 1.8)
2. ❌ But at the cost of letting enemies capture junctions
3. ❌ And exploring less aggressively

**Why this happens:**
- On-policy RL optimizes recent experiences
- If recent rollouts had lots of deaths → learn to avoid dying
- But this creates a **conservative policy** that doesn't pursue the objective
- The agent "forgot" that dying is acceptable if you win more junctions

## Composite Score Formula (Hypothesis)

Based on the metrics, composite_score likely weighs:
- ✅ **Clips junctions held** (positive, both runs ~1.2M)
- ❌ **Cogs junctions held** (negative penalty, 30-min has 162.8)
- 💰 **Resources** (carbon, hearts - 30-min has less)
- 🏃 **Activity** (cells visited, successful moves - 30-min is more passive)

The 14.6 point drop comes from:
- Enemy controlling junctions (-5 to -10 points?)
- Less resources (-2 points?)
- Less exploration/activity (-2 to -5 points?)

## Why Training Metrics Don't Catch This

**Training losses measure:**
- Policy loss: how well updates fit recent rollouts ✅
- Value loss: how well critic predicts returns ✅
- Entropy: behavioral diversity ✅

**But they DON'T measure:**
- Strategic objective achievement ❌
- Long-term consequences of conservative play ❌
- Whether the policy "forgot" earlier aggressive strategies ❌

## Solutions

### 1. Reward Shaping
Add explicit penalties for:
- Allowing enemy junction control (currently might be too weak)
- Passive play / low exploration
- Resource mismanagement

### 2. Curriculum Learning
Mix rollouts from:
- Current policy (conservative)
- Earlier checkpoints (aggressive)
- Force policy to "remember" aggressive strategies

### 3. Multi-Objective Optimization
Track multiple metrics:
- Junction control ratio
- Exploration coverage
- Resource efficiency
Optimize for all, not just total reward

### 4. Regularization
- Add KL penalty to prevent large policy shifts
- Behavioral cloning loss toward best checkpoint
- Maintain "aggressive exploration" baseline

### 5. Value Function Fix (what we're testing in Exp 2)
- Slower value updates = more stable advantage estimates
- Better critic → better policy gradients → less drift

## Recommended Next Steps

1. ✅ **Test dual learning rates** (Exp 2 running now)
2. Analyze if dual LR maintains aggressive strategy
3. If not, try **KL penalty** or **behavioral cloning** toward epoch 330
4. Consider **reward shaping** to explicitly penalize passive play
5. Implement **checkpoint evaluation** to catch degradation early

---

**Key Insight:** The policy isn't "breaking" - it's learning to optimize the wrong thing (safety over objectives). This is a reward/optimization mismatch, not a pure training stability issue.
