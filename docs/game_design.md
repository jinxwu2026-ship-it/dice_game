# The King's Gambit — Version 1 Game Design

# 《国王的赌局》——第一版游戏设计

## 1. High concept / 核心概念

*The King's Gambit* is a short medieval dice roguelite. The player challenges a sequence of gamblers and repeatedly makes one central decision:

《国王的赌局》是一款短流程的中世纪骰子 Roguelite。玩家依次挑战多名赌徒，并反复面对一个核心选择：

> Bank the current points safely, or roll again for a larger reward and risk losing the unbanked points?

> 安全地保存当前分数，还是继续掷骰争取更高收益，并承担失去本回合临时分数的风险？

Every major feature should strengthen this roll-versus-bank decision. Features that do not support it are outside Version 1.

所有主要功能都应服务于“继续掷骰还是保存分数”的选择。不能强化这一选择的功能不进入第一版。

## 2. Target experience / 目标体验

- A successful run lasts approximately 12–18 minutes.
- The rules are easy to understand, while risk management creates tension.
- The player makes simple choices; calculations and state updates are automatic.
- Rewards allow a small build to form during each run.
- The medieval presentation gives the game a clear identity without adding a movement system or map exploration.

- 完整通关约需 12–18 分钟。
- 规则容易理解，但风险管理能够制造紧张感。
- 玩家只负责做选择，计算和状态更新由程序自动完成。
- 奖励让玩家在每局内形成简单构筑。
- 中世纪表现风格提供明确特色，但不加入角色移动或地图探索。

## 3. Run structure / 单局流程

A run uses a fixed sequence of five encounters:

一局采用固定的五场对战流程：

```text
Encounter 1: Normal opponent
第一场：普通对手
        ↓
Choose one reward
三选一奖励
        ↓
Encounter 2: Normal opponent
第二场：普通对手
        ↓
Shop
商店
        ↓
Encounter 3: Elite opponent
第三场：精英对手
        ↓
Choose one reward
三选一奖励
        ↓
Encounter 4: Strong opponent
第四场：强力对手
        ↓
Rest or shop
休息或商店
        ↓
Encounter 5: Boss
第五场：Boss
```

The player begins with 3 HP. Losing an encounter removes 1 HP. Reaching 0 HP ends the run; defeating the boss wins the run.

玩家以 3 点生命开始。输掉一场对局失去 1 点生命。生命归零时本局失败；击败 Boss 时本局胜利。

Version 1 has no branching map or permanent progression between runs.

第一版不包含分支地图，也不包含跨局永久成长。

## 4. Match objective / 对局目标

The player and opponent take turns rolling dice. The first side to reach the match target wins. The current balance target is approximately 2,000 points.

玩家和对手轮流掷骰。率先达到目标分数的一方获胜；当前暂定目标约为 2,000 分。

Each opponent has:

每名对手拥有：

- A name and medieval personality.
- A banking threshold controlling how much risk the AI accepts.
- An optional small passive ability for stronger encounters.

- 名称与中世纪人物风格。
- 一个存分阈值，用于决定 AI 愿意承担多少风险。
- 强力对手可以拥有一个简单的被动能力。

The AI should remain understandable and deterministic enough to explain. Machine learning is unnecessary.

AI 应当容易理解和解释，不需要机器学习。

## 5. Player turn / 玩家回合

1. Roll six dice.
2. Select a valid scoring subset.
3. Add the selected value to the unbanked round score.
4. Choose to roll the remaining dice again or bank the round score.
5. If a new roll contains no scoring dice, the player busts and loses the unbanked round score.
6. Banking adds the round score to the match total and ends the turn.

1. 掷出六颗骰子。
2. 选择一个有效的计分骰子组合。
3. 将其分数加入本回合尚未保存的分数。
4. 选择继续投掷剩余骰子，或保存本回合分数。
5. 如果新一次投掷没有任何可计分骰子，玩家爆骰并失去本回合未保存分数。
6. 保存分数会把本回合分数加入对局总分，并结束玩家回合。

The scoring system uses a small, clearly documented Farkle-style ruleset. Version 1 should begin with single 1s, single 5s, and three-of-a-kind. Extra combinations should be added only after the basic scoring validator is reliable.

计分采用简化且清楚说明的 Farkle 风格规则。第一版先支持单个 1、单个 5 和三颗相同骰子；只有在基础计分验证稳定后，才考虑增加其他组合。

## 6. Player decisions / 玩家决策

The normal turn contains only three actions:

普通回合只包含三类操作：

- Select dice by position.
- Roll again.
- Bank the current score.

- 按位置选择骰子。
- 继续掷骰。
- 保存当前分数。

The player does not manually calculate points or update status. The program validates selections, calculates scores, runs opponent turns, applies effects, and redraws the interface.

玩家不需要手动计算或更新状态。程序负责验证选择、计算分数、执行对手回合、应用效果并刷新界面。

## 7. Gamebar / 游戏界面

Version 1 uses one continuously updated gamebar rather than several complex menus.

第一版使用一个持续更新的 gamebar，而不是多个复杂菜单。

```text
+----------------------------------------------------------+
|                    THE KING'S GAMBIT                     |
+----------------------------------------------------------+
| OPPONENT                                                 |
| Noble Gambler                              HP: 2 / 3     |
| Score: 1350 / 2000                                       |
| [####################----------]                         |
|                                                          |
| Opponent's dice                                          |
|      [3]      [5]      [1]      [6]      [2]      [4]   |
+----------------------------------------------------------+
| ROUND 3                                                  |
| Current round score: 450                                 |
|                                                          |
| Your dice                                                |
|      [1]      [5]      [2]      [1]      [6]      [5]   |
|       ^                ^                 ^               |
|    selected         selected          selected           |
|                                                          |
|       [R] Roll again              [B] Bank 450           |
+----------------------------------------------------------+
| PLAYER                                                   |
| Score: 850 / 2000                          HP: 3 / 3     |
| Relic: Lucky Coin                  Gold: 45              |
+----------------------------------------------------------+
```

The gamebar displays:

gamebar 显示：

- Opponent name, score, status and latest dice.
- Round number and unbanked score.
- Player dice and selected positions.
- Available actions and short result messages.
- Player score, HP, gold and relics.

- 对手名称、分数、状态和最近一次骰子结果。
- 回合编号和尚未保存的分数。
- 玩家骰子和已选择位置。
- 当前可用操作和简短结果提示。
- 玩家分数、生命、金币和遗物。

## 8. Rewards and shop / 奖励与商店

After selected encounters, the game presents three rewards and the player chooses one. Version 1 contains only a small set of rewards.

完成指定对局后，游戏提供三个奖励，玩家选择其中一个。第一版只制作少量奖励。

Reward categories:

奖励类型：

- Relic: changes rolling, banking, scoring or survival.
- Special die: slightly changes the probability or value of a roll.
- Healing: restores 1 HP.
- Gold: used only in one simple shop.

- 遗物：改变掷骰、存分、计分或生存能力。
- 特殊骰子：轻微改变掷骰概率或结果价值。
- 治疗：恢复 1 点生命。
- 金币：仅用于一个简单商店。

Recommended Version 1 limit:

第一版建议上限：

- 3–5 relics.
- 2–3 special dice effects.
- One shop with a small selection.

- 3–5 个遗物。
- 2–3 种特殊骰子效果。
- 一个只出售少量物品的商店。

## 9. Technology decision / 技术选择

The safe baseline is a Python standard-library CLI with an ASCII gamebar. This version should remain fully playable without third-party libraries.

最安全的基础方案是使用 Python 标准库和 ASCII gamebar 的命令行游戏，并确保不依赖第三方库也能完整游玩。

PyGame may be used for visual presentation only if the tutor approves it. If used, the game rules should remain separate from the PyGame display layer so the core logic can still be tested independently.

如果 tutor 批准，可以使用 PyGame 改善视觉表现。游戏规则必须与 PyGame 显示层分离，使核心逻辑仍可独立测试。

PyGame would display dice, buttons, scores and status; it should not change the scope of the gameplay.

PyGame 只负责显示骰子、按钮、分数和状态，不应扩大游戏玩法范围。

## 10. Project structure / 项目结构

The project is divided into seven code modules:

项目拆分为七个代码模块：

```text
the_kings_gambit/
|-- main.py          # Entry point and main menu / 程序入口与主菜单
|-- dice.py          # Dice rolling / 掷骰
|-- scoring.py       # Validation and scoring / 验证与计分
|-- models.py        # Player and opponent state / 玩家与对手状态
|-- battle.py        # Turns, AI and match flow / 回合、AI 与对局流程
|-- progression.py   # Encounters, rewards and shop / 对战、奖励与商店
|-- ui.py            # ASCII display and input / ASCII 显示与输入
|-- tests/
|   |-- test_dice.py
|   `-- test_scoring.py
`-- README.txt       # Run instructions / 运行说明
```

Responsibility boundaries:

职责边界：

- `main.py` starts the program but does not calculate scores.
- `scoring.py` calculates scores but does not read player input.
- `ui.py` displays and collects input but does not implement game rules.
- `battle.py` coordinates turns by calling the smaller modules.
- `progression.py` controls the five-encounter run, not individual dice calculations.

- `main.py` 启动程序，但不计算分数。
- `scoring.py` 计算分数，但不读取玩家输入。
- `ui.py` 显示内容并接收输入，但不实现游戏规则。
- `battle.py` 通过调用其他模块来组织回合。
- `progression.py` 管理五场对战流程，不负责单次骰子计算。

## 11. Development order / 开发顺序

Build the smallest independent rules first:

先完成最小且可独立测试的规则：

1. Dice rolling.
2. Scoring and selection validation.
3. Player and opponent state.
4. ASCII display and input validation.
5. One complete player-versus-AI match.
6. Rewards, shop and five-encounter progression.
7. Main menu, victory screen, defeat screen and final documentation.

1. 掷骰。
2. 计分与选择验证。
3. 玩家和对手状态。
4. ASCII 显示与输入验证。
5. 一场完整的玩家对 AI 对局。
6. 奖励、商店和五场对战流程。
7. 主菜单、胜利界面、失败界面和最终文档。

## 12. Version 1 exclusions / 第一版排除内容

- Branching route map.
- Character movement or exploration.
- Networking or multiplayer.
- Large inventory systems.
- Many characters, relics or dice types.
- Complex animation and audio systems.
- Permanent progression between runs.

- 分支路线地图。
- 角色移动或探索。
- 网络功能或多人游戏。
- 大型背包系统。
- 大量角色、遗物或骰子种类。
- 复杂动画和音频系统。
- 跨局永久成长。

## 13. Completion criteria / 完成标准

Version 1 is complete when:

第一版满足以下条件时视为完成：

- A player can finish a five-encounter run.
- Dice rolls, scoring and selection validation work correctly.
- Roll, bank and bust outcomes update the correct state.
- The AI completes its turns automatically.
- HP, scores, gold, rewards and relic effects update correctly.
- The gamebar reflects every important state change.
- The boss can be defeated and zero HP ends the run.
- Victory and defeat summaries are displayed.
- Invalid input does not crash the program.
- The program includes clear instructions for the tutor.

- 玩家可以完成一局五场对战。
- 掷骰、计分和选择验证正确工作。
- 继续掷骰、保存分数和爆骰会正确更新状态。
- AI 能自动完成回合。
- 生命、分数、金币、奖励和遗物效果正确更新。
- gamebar 能反映所有重要状态变化。
- 玩家能够击败 Boss，生命归零会结束游戏。
- 游戏显示胜利与失败总结。
- 无效输入不会导致程序崩溃。
- 程序包含供 tutor 使用的清楚运行说明。

## 14. Final design rule / 最终设计原则

> If a feature does not make the decision to roll or bank more interesting, it does not belong in Version 1.

> 如果一个功能不能让“继续掷骰还是保存分数”的决定更有趣，它就不应该进入第一版。
