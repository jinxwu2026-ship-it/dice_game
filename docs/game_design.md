# The King's Gambit — Version 1 Game Design

# 《国王的赌局》——第一版游戏设计

> Design revision / 设计修订：2026-09-21。
> 已合并用户提供的计分与 AI 设计；精确规则见 [game_rules.md](game_rules.md)。
> 当前单人练习已实现新版基础规则与 Bank 达到 2,000 的胜利条件。
> 本阶段按用户要求不实现任何 AI；五关、HP、奖励与完整 gamebar 仍为目标设计。
> 原文与数值出处见 [归档参考](scoring_and_ai_reference.md)。

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

The player and opponent alternate turns. The first side to bank a total of at least 2,000 points wins immediately. Unbanked points cannot win a match.

玩家和对手轮流掷骰。默认目标为 2,000 分，Bank 后总分达到或超过目标立即获胜；未保存分数不能判胜。

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

1. Start with six fair dice and an unbanked Turn Score of zero.
2. After rolling, bust only if there is neither a positive scoring choice nor an ordinary three-pair action.
3. The player chooses positions first; validate and score only that selection.
4. Add the points, set the selected dice aside, then bank or roll the remaining dice.
5. If a positive selection consumes all available dice, restore six dice; bank or continue with the accumulated score still at risk.
6. An explicit ordinary three-pair action adds zero, preserves the earlier Turn Score and rerolls six dice.
7. Banking transfers the Turn Score and ends the turn; a bust loses it and passes play to the opponent.

1. 以六颗公平六面骰和 0 分 Turn Score 开始。
2. 掷骰后，仅在没有正分合法选择、也没有普通三对动作时 Bust。
3. 玩家先按位置选骰，程序只验证并结算所选集合，不自动替玩家拿最高分。
4. 加分并取走所选骰后，选择 Bank 或重掷剩余骰。
5. 正分选择耗尽当前所有可用骰时恢复六骰，可 Bank 或继续；累计分数仍有风险。
6. 显式发动普通三对得到 +0、保留此前 Turn Score，并重掷六骰；不额外插入 Bank 阶段。
7. Bank 转移分数并结束回合；Bust 丢失本回合未存分并换手。

### 5.1 Scoring / 计分设计

下表概述目标规则，完整分值、优先级与非法选择以 [game_rules.md](game_rules.md) 为准。

| 组合 | 新分值 / 效果 |
|---|---|
| 单 1 / 单 5 | 100 / 50 |
| 三同号 1 / 2 / 3 / 4 / 5 / 6 | 500 / 200 / 300 / 400 / 500 / 600 |
| 四至六同号 | 三同号基础分 + 200 × (同号数 − 3)，整体计分 |
| 12345 / 23456 / 123456 | 500 / 600 / 1200 |
| 普通三对（非三连对） | 显式选择全部六骰，放弃本次直接得分，+0 并重掷六骰 |
| 112233 / 223344 / 334455 / 445566 | 1200 / 1000 / 1100 / 1200，均触发 Hot Dice |
| 两组三同号 | 两组相加，无额外奖励；耗尽骰池触发 Hot Dice |

每颗选中骰只能消耗一次，不能跨掷骰拼组合。判定顺序为六骰整体组合、五骰顺子、
三至六同号、剩余单 1 / 5；任何未被合法消耗的所选骰都会使整个选择非法。
顺子外的单 1 / 5 可叠加，组合内部不能重复得分。普通三对不强制覆盖正分子集：
`113366` 可只取 `11` 得 200、剩四骰，或明确发动整组 +0 重掷。

单人练习已完成同号和顺子数值迁移，并加入普通三对、三连对与相应回归测试。

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

普通三对属于选骰动作中的显式功能选择，必须提示“本次 +0，保留此前分数，重掷六骰”。
例如 `333566` 可选 `3335` 得 350、剩两骰，也可只选 `5` 得 50、剩五骰；
UI 可展示两者的得分与剩余骰数，但最终由玩家决定。

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
- Player dice, selected positions, dice available next, and Hot Dice status.
- Available actions and short result messages.
- Player score, HP, gold and relics.

- 对手名称、分数、状态和最近一次骰子结果。
- 回合编号和尚未保存的分数。
- 玩家骰子、已选择位置、下次可用骰数和 Hot Dice 状态。
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

提高骰池数量同时影响即时得分、Bust 与组合概率，不能按“多一颗单骰的分值”定价。
来源文件的扩骰建议仅作未来平衡参考；V1 基础骰池保持六骰，不在本次新增扩骰遗物。
奖励叠加顺序和败局后重置流程仍待实现阶段决定。

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
`-- ui.py            # ASCII display and input / ASCII 显示与输入
tests/
|-- test_dice.py
`-- test_scoring.py
README.md            # Run instructions / 运行说明
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

### 10.1 Shared action contract / 共享动作接口

沿用七模块结构，不要求照搬原文的类层次。`scoring.py` 提供纯函数验证与合法动作枚举；
单个动作至少描述 `selected_positions`、`score_delta`、`dice_left`、`hot_dice`、
`action_type`（正分选择或普通三对重掷）。非法结果单独表示，不能与合法 +0 混同。
计分层可计算动作元数据，但实际状态变更交给回合引擎。

`models.py` 保存双方已存分、Turn Score、可用骰数、当前掷骰与行动阶段；
`battle.py` 应用动作、处理 Bank / Bust / 换手 / 胜利与 AI 决策。
UI、AI 和未来模拟器共用计分动作，不复制计分表。掷骰前的 Bank / Roll 决策
与掷骰后的选骰应分开，避免在看见失败结果后允许反悔 Bank。
当前 `calculate_score` 返回 `None` 表示组合非法，返回 `0` 表示合法普通三对；
非法骰值仍抛出 `ValueError`。`score_selection` 对非法选择抛出 `ValueError`，
允许合法 0 分。`selection_action` 返回上述元数据，`enumerate_legal_selections`
枚举当前掷骰的位置子集，`is_bust` 根据是否存在合法动作判断。

`TurnState.phase` 使用 ready / select / decision / ended 四个阶段；
`begin_roll` 提交并保存当前骰型后禁止 Bank，`resolve_roll` 只结算该骰型的选择。
正分动作进入 decision，普通三对进入 ready 并由练习循环立即重掷。
为兼容原测试接口，未保存待选骰型时 `resolve_roll` 也可一次提交并结算新掷骰；
此调用表示新掷骰，不能用来追加选择上一掷骰的剩余骰子。

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
- Dice rolls, all revised scoring combinations and selection validation work correctly.
- Roll, bank and bust outcomes update the correct state.
- The AI completes its turns automatically.
- HP, scores, gold, rewards and relic effects update correctly.
- The gamebar reflects every important state change.
- The boss can be defeated and zero HP ends the run.
- Victory and defeat summaries are displayed.
- Invalid input does not crash the program.
- The program includes clear instructions for the tutor.

- 玩家可以完成一局五场对战。
- 掷骰、全部修订计分组合和选择验证正确工作，包括普通三对 +0 与连续 Hot Dice。
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


## 15. Integration decisions / 合并分析与采用边界

本次用户请求将新规则纳入设计，因此旧计分数值由新方案替代；已确认的固定阈值 AI
仍用于 V1。原文中以“建议”“可采用”表述的高阶策略保留为演化方向，不自动成为必做功能。

| 项目 | 旧设计 | 合并后设计 |
|---|---|---|
| 111 | 1000 | 500，降低安全面同时拥有的爆发优势 |
| 四至六同号 | 每多一骰翻倍，最高 8000 | 每骰 +200，单个同号组合最高 1200 |
| 23456 / 123456 | 750 / 1500 | 600 / 1200，适配 2000 胜利线 |
| 普通三对 | 无独立动作 | 可选 +0 重掷，既有 Turn Score 保留 |
| 三连对 | 无专属分值 | 四种固定分值 1000–1200，并恢复六骰 |
| 合法性 / Bust | 用正分区分合法与否 | 合法 +0 与非法分开，按有无合法动作判 Bust |
| AI Bank | 固定 score ambition，能赢即存 | 保留；采用原文 Easy 的最高即时分选骰 |
| Normal / Hard | 未纳入 | 收录为后续研究，不改变 V1 验收范围 |
| 原文次优动作采样 | 与确定性要求不兼容 | 不采用；随机性仍只来自骰子 |

普通三对原文“重新获得并投掷”的表述在本次规范中解释为立即重掷；
它与普通正分 Hot Dice 的 Bank / Roll 选择明确区分，避免实现时产生两种行为。
五关、3 HP、奖励、商店、标准库 CLI 与可测试核心边界保持原设计。

## 16. Balance analysis / 数值分析

以下数据转述自[原始参考](scoring_and_ai_reference.md)，**未在本项目独立复现**。
来源称组合概率采用 46,656 个六骰有序结果枚举，策略数据来自约 20 万回合模拟；
未提供复现脚本与完整参数。不得将这些数字当作已验证的 AI 参数或验收断言。
概率指骰型中存在机会，不代表玩家必选，也不等于整回合实际触发率。

| 可掷骰数 | 来源：最高即时期望分 | 来源：Bust 率 |
|---:|---:|---:|
| 6 | 346.4 | 约 2.315% |
| 5 | 215.3 | 7.72% |
| 4 | 134.0 | 15.74% |
| 3 | 84.5 | 27.78% |
| 2 | 50.0 | 44.44% |
| 1 | 25.0 | 66.67% |

来源给出：大顺子约 1.543%、任意三连对约 0.772%、普通三对约 3.086%；
六骰普通三对减少的 Bust 约 0.579 个百分点，总 Hot Dice 机会约 10.11%。
这些事件可能与其他可选子集重叠，不可把概率无条件相加。

设计意义是保留骰子也有价值，少取分并非无效操作。`333566` 的 350 分两骰
与 50 分五骰构成实际取舍；不能把“取最高即时分”说成玩家总是最优的选择。
来源估计五骰增至六骰的即时价值增加约 131.1，但这不是第七骰的价值。
来源的固定骰面边际值显示 5 可能因组合参与度略高于 1；这是分布下的统计结论，
不是每个局面中的固定排序。完整概率、骰面边际值和模拟表保留在归档中。

## 17. AI roadmap / AI 演化路线

### 17.1 V1 / Easy：确定性基线

合法动作中取即时分最高者；同分按固定位置顺序（实现时确定并测试）。
没有正分但有普通三对时发动重掷。正常决策点先检查是否可 Bank 获胜，
再检查 Turn Score 是否达到 score ambition，否则继续掷骰。
不同对手可配置不同 ambition；具体数值待测试，不使用隐藏随机选择。

### 17.2 Normal：未来价值、风险人格与局势（后续方向）

考虑每个动作的新增分 `s_a` 与后续可用骰数 `n_a`，而非只比较即时分。
研究基线为回合期望模型：

```text
V_bank(T, n) = T
V_roll(T, n) = sum_r P(r) * max_a V(T + s_a, n_a)
V(T, n) = max(V_bank, V_roll)
```

无合法动作的 Bust 项取 0；耗尽骰池后 `n_a=6`。普通三对 +0 是强制重掷动作，
其后继应进入 `V_roll(T,6)`，不能直接套允许 Bank 的 `V(T,6)`。
此修正体现本次明确的动作阶段，原文数值不可未经复算直接沿用。
来源的纯期望阈值（按剩余 1–6 骰）约为 300、250、400、950、3050、15000；
它不考虑实际 2000 胜利终止，不能用来覆盖 V1 ambition。能 Bank 获胜始终优先。

后续可研究 `U(x)=(x/R)^gamma`，其中 R 为关注的正目标分数，
gamma 为 0.5 / 1 / 2 分别示意保守 / 中性 / 激进。
来源模拟的平均 Bank 分为 481 / 492 / 379，0 分回合为 10.2% / 17.3% / 66.0%；
激进强调高分尾部而非较高均值，不能把激进简单等同于更强 AI。

局势应从 AI 自身视角定义：`gap = self_score - other_score`，
`other_need = target - other_score`。来源建议分差约 ±250 为中性区；
领先 250–600、600–900、900+ 逐渐保守，落后 250–600、600–800、800+
逐渐激进；对方仅差 250 时进入紧急状态、差 500 时提高风险、差 800 以上以分差为主。
这些是待验证的启发式区间，边界优先级与人格参数要另行定义，尚不是可执行规格。
来源关于对方差 250 / 500 / 800 / 900 的下一回合成功率约 83% / 49% / 14% / 10%，
依赖其模拟策略，不能等同于本项目 V1 对手的真实威胁概率。

### 17.3 Hard / 平衡基准：最终胜率（后续方向）

以当前行动方视角定义 `W(S_self, S_other, T, n)` 为最终胜率：

```text
Q_bank = 1                                      if S_self + T >= target
Q_bank = 1 - W(S_other, S_self + T, 0, 6)        otherwise
Q_bust = 1 - W(S_other, S_self, 0, 6)
Q_select(a) = W(S_self, S_other, T + s_a, n_a)
```

选骰后对合法动作取最大值，掷骰前按结果概率求和；普通三对仍直接进入重掷阶段。
新回合 `T=0,n=6` 必须先掷骰，不能因为套用通式而允许空 Bank。
换手的 `1-W` 假设双方遵循同一胜率模型；若研究不同人格对战，需在状态中区分策略。
此方向让领先保护、落后翻盘和残局冒险由胜率目标产生，不要求 V1 实现求解器。

基础分均为 50 的倍数，可在无修饰规则下按 50 压缩状态；每种骰子多重集合需按
`n! / product(count!) / 6**n` 加权，不能把不同多重集合当作等概率。
可预计算合法动作，用值迭代或策略迭代处理 Hot Dice 和普通三对循环；不能仅用朴素递归。
引入遗物后必须重新检查离散化、骰面概率与终止条件，不能复用不适用的基础表。

## 18. Migration and validation / 迁移与验证

单人练习已迁移分值、合法动作表示、Bust、回合状态、UI 提示与回归测试，
并支持仅通过 Bank 达到 2,000 分结束练习。当前版本不含任何 AI。
剩余完整游戏任务见 [TODO.md](../TODO.md)。
新规则测试矩阵见 [game_rules.md 第 6 节](game_rules.md#6-实现顺序与验收)。
复现概率时记录规则版本与事件定义；模拟时记录策略、随机种子、样本量和误差；
求解时记录截断、收敛条件与强制重掷语义。基础规则测试通过不代表统计模拟已复现，
也不代表包含对手、HP 和五关的完整 V1 已完成。
Normal / Hard 的 `333566` 状态相关最优动作测试留到相应策略实现时，不能要求 Easy 改变固定行为。
