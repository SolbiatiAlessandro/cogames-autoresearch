# CoGames: Cogs vs Clips Overview

## What is it?
Multi-agent cooperative territorial control game. Part of the Alignment League
Benchmark (ALB) by Softmax/Metta-AI. Teams of AI agents (Cogs) compete against
automated opponents (Clips) to capture and hold territory.

## Core Mechanics

### Territory Control
- Map contains **junctions** that can be neutral, allied, or enemy
- Facilities project area-of-effect (AOE) in radius ~10 cells
- Within friendly territory: full HP + energy restore
- Outside friendly territory: -1 HP per tick, energy drains
- Clips continuously expand, creating constant pressure

### Roles (acquired at Gear Stations)
| Role      | Bonus           | Job                                    |
|-----------|-----------------|----------------------------------------|
| Miner     | +40 cargo       | Extract resources from extractors      |
| Aligner   | —               | Capture neutral junctions (costs heart)|
| Scrambler | +200 HP         | Disrupt enemy junctions (costs heart)  |
| Scout     | +100 energy     | Mobile reconnaissance, +400 HP         |

### Economy Flow
1. **Miners** extract resources (carbon, oxygen, germanium, silicon)
2. Resources deposited at aligned junctions / hub
3. **Hearts** crafted at Assembler from resources
4. **Aligners** spend hearts to capture neutral junctions
5. **Scramblers** spend hearts to neutralize enemy junctions

### Scoring
- Reward per tick = aligned_junctions_held / max_steps
- This is the "objective" reward — the ground truth metric
- More territory held for longer = higher score

## Key Training Challenges
1. **Role specialization**: agents must learn to pick different roles
2. **Sequential dependencies**: miners → resources → hearts → aligners → territory
3. **Coordination**: no single role succeeds alone
4. **Sparse reward**: territory capture only happens after a chain of precursor behaviors
5. **Clips pressure**: agents must defend while expanding

## Available Missions
- `training_facility_open_1` — tiny map, fast iteration (2 agents)
- `cogsguard_machina_1.basic` — standard benchmark (4 agents)
- `cogsguard_machina_1.*` — various difficulty variants
- Large candidate maps (500x500, 1000x1000) for final evaluation

## Policy Architecture
- Default: PufferLib CNN+LSTM (pufferlib.models.Default)
- Input: grid observation (what the agent sees)
- Output: action distribution (move N/S/E/W, rest)
- Parameter sharing across agents (same policy for all)
