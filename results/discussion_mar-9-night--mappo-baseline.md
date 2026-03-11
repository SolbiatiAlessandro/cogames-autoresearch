## Session mar-9-night--mappo-baseline — Mar 9-10, 2026

**Direction:** Build strong MAPPO baseline, fight reward hacking, get miners to actually mine and deposit resources to base.

**Prior findings:** Previous sessions established that high composite scores (200-300+) were mostly reward hacking — agents score high by collecting resources but hold ZERO territory. The lean combo (no credit/scout) with score ~54.9 was the first to show aligner_gained=0.2, indicating real gear pickup.

**Plan:**
- 5-min experiments (300s budget) to find configs with actual game progress
- Focus metrics: miner_gained, carbon_deposited, aligned_by_agent
- Target: get miners to pick up gear AND deposit resources to base

## Experiment Log

### Phase 1: Finding the right reward combo (Claude Code, Mar 9 night)
The autonomous agent ran ~9 experiments exploring reward variant combinations. Due to a bug in the experiment loop (commits happened before runs, results never written to results.tsv), only the commit messages survive as evidence. Key progression:

1. **milestones_2 + role_conditional + penalize_vibe_change + miner** (lean honest baseline) — starting point
2. **+ent_coef=0.05** — more exploration
3. **+vf_coef=4.0** — stronger critic
4. **+scout** — this was the breakthrough combo
5. **20min budget** — scale up
6. **+aligner** — target alignment behavior
7. **ent_coef=0.08** — push exploration further
8. **bptt=128** — longer memory for multi-step planning
9. **10min budget, no aligner** — sweet spot test

Machine crashed ~3am, ending the session. No results.tsv rows were written for any of these experiments.

### Phase 2: Manual verification (Tashi/OpenClaw, Mar 10 evening)
Re-ran the final commit (bf43952) to get actual numbers:

**Config:** milestones_2 + role_conditional + penalize_vibe_change + miner + scout | ent_coef=0.05, vf_coef=4.0, bptt=128, 10min budget

**Results:**
- **composite_score: 304.1**
- cogs_junctions_held: 0
- aligned_by_agent: 0
- carbon_deposited: 2.5
- miner_gained: 0.2, aligner_gained: 0.2, scrambler_gained: 0.2, scout_gained: 0.2
- deaths: 1.7, cells_visited: 3M+

**Replay analysis (1000 steps):**
Agents are picking up gear (miner x2, aligner x3, hearts x4) and exploring the map actively. They differentiate roles — some mine, some scout. But they lose all gear by end (gained=lost) suggesting they die or drop it. The behavior is qualitatively different from prior sessions: agents now actually use the role system and mine resources, rather than just wandering. Score is still composite-reward-driven rather than territory-driven.

### Key Insight
The **miner + scout** reward shaping combo teaches agents to differentiate roles and actually interact with the environment (pick up gear, mine resources). This is a meaningful behavioral improvement even though junctions_held is still 0. The next step is bridging from "agents mine and explore" to "agents hold territory" — possibly by adding junction-holding rewards or reducing the weight of mining/scouting rewards once agents have learned the basics.

### What Didn't Work / Open Questions
- **aligner reward** — unclear if it helped or hurt (was removed in final experiment). Need an A/B test.
- **bptt=128** — longer memory should help multi-step planning but unclear impact on score
- **20min budget** — didn't clearly outperform 10min; may be diminishing returns or LR schedule issue
- **credit reward** — present in earlier high-scoring experiments but removed in this session. Was it helping?

## INFRA
- **Machine crash** killed the session at ~3am. No data loss prevention — results.tsv was never updated during the session.
- **Root cause of missing results:** The experiment loop in program.md had commits *before* runs. Claude Code committed train.py, then ran training, but never wrote results back. Fixed in program.md (run first, then commit train.py + results.tsv atomically).
- **gh CLI not available** on previous machine setup, so GitHub Discussions were never posted. The agent wrote a local discussion file in results/ as fallback (which worked).
- **Watchdog scripts** were deleted mid-session by the agent as part of a "simplify" refactor, breaking the cron-based monitoring.
