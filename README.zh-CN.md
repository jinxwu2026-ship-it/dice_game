# The King's Gambit

[English](README.md) | **简体中文**

继续掷骰争取更多分数，还是及时收手保住收益？在窗口或终端中挑战完整的五场骰子冒险。

## 快速运行

安装 **Python 3.10 或更新版本**（当前验证环境为 Python 3.12.10）。下载或克隆本仓库后，
在包含 `main.py` 和 `requirements-gui.txt` 的项目根目录打开终端。
下面的命令会创建本地虚拟环境，并安装窗口版唯一的外部依赖 **pygame-ce 2.5.8**，无需手动激活环境。

### Windows（PowerShell）

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-gui.txt
.\.venv\Scripts\python.exe main.py --gui
```

安装完成后，再次游玩只需执行最后一行。如果 Windows 无法识别 `python`，第一行可改用 `py`。

### macOS / Linux

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements-gui.txt
./.venv/bin/python main.py --gui
```

这些是对应平台的标准虚拟环境命令，尚未验证 macOS/Linux 桌面上的实际游玩。
Linux 的 Python 安装需要提供 `venv` 模块。

### 开始游玩

在主菜单选择 **New Run**。领取或跳过开局骰子，再选择赌注；允许以 0 金币开始战斗。战斗中：

1. 点击骰子，将其移入左侧选择区；再次点击可以撤回。
2. 点击 **Confirm +N**，确认一个合法的得分选择。
3. 点击 **Bank** 保住本回合分数，或点击 **Roll** 继续冒险。
   Bust 会失去本回合未入账的分数；Bank 和 Bust 后会自动切换回合。

主菜单和游玩界面的 **Rules** 都可以查看图示计分规则。
中文版 README 只翻译说明文档，游戏界面仍为英文。

### 终端版（无需外部依赖）

以下命令不需要安装 pygame。Windows 使用 `python`；macOS/Linux 请改用 `python3`。

```powershell
python main.py --run       # 完整五场冒险
python main.py --help     # 查看命令行参数
```

输入骰子位置，如 `1 3 5`；确认后输入 `R` 继续掷骰，或 `B` 收手入账。
终端版在回合结束后按 Enter 继续，`Q` 退出。`--ascii` 将特殊符号换成字母；
`--ai-delay 0` 取消默认的每次 AI 动作 2 秒停顿。

窗口版和终端版都会把实际对局保存为 `match_logs/` 下的本地 `.txt` 文件。
当前不支持保存并恢复尚未结束的冒险。

用于课程提交时，图形界面需要在有桌面显示的本地电脑运行，不能直接在 Ed 执行环境中运行。
分享窗口版时，请包含 `main.py`、整个 `the_kings_gambit/` 包、`assets/` 和
`requirements-gui.txt`，不要包含 `.venv/` 或个人 `match_logs/` 文件。

公开仓库只包含运行代码、必需图片、双语 README 和依赖文件。
设计文档、界面截图、测试、分析工具、本地环境及个人记录保留在开发目录，不上传。
下文标记为“仅本地”的引用指开发目录中的文件，不属于公开仓库内容。

## 游戏介绍

*The King's Gambit* 是一款简短的中世纪骰子 Roguelite，灵感来自《天国：拯救 2》的骰子小游戏。
玩家按固定顺序挑战五名对手，核心选择是：继续掷骰争取更高收益，还是收手将当前分数安全入账。

游戏提供仅使用 Python 标准库的命令行界面，以及可选的 pygame-ce 鼠标界面。
两种界面共用规则与流程控制器。

## 窗口界面

英文主菜单提供 **New Run**（开始冒险）、**Leaderboard**（排行榜）、**Rules**（规则）、
**Quit**（退出）。界面采用简约 V3 设计：细线分隔、52 像素骰子，左下方显示 HP/金币，
左上方显示双方分数，顶部中央显示对手图案，右上方显示本回合分数。

场上只展示当前行动方的骰子。点击可选骰子后，它会移到左侧选择区；再次点击可撤回。
**Confirm +N** 提交当前预览，**Clear selection** 清空尚未确认的选择。
只有确认后才会出现 **Roll N** / **Bank S**，同时显示风险分和入账后的总分。
普通三对改为提供 **Reroll Six (+0)**。悬停或聚焦骰子可查看效果和实际骰面概率；禁用按钮不能提交动作。

使用 **Tab / Shift+Tab** 或方向键移动焦点，**Enter / Space** 激活，**1–6** 切换对应固定槽位的骰子。
焦点以角标显示，选中的骰子带勾选标记。成长相关界面也支持键盘焦点操作。

游玩时可从右上方打开 **Rules**。两页图示通过真实骰面展示单颗计分、三同、额外同点骰、顺子和对子。
例如三个 3 显示 300 分，再增加一个 3 显示 +200。分数由共用计分器提供。
关闭规则后保留当前未确认的选择；规则打开期间暂停自动切换回合，但 AI 仍会在后台行动。
Escape 关闭最上层窗口，关闭游戏的确认框会叠加在规则上方。
同点骰规则图 (仅本地: `docs/ui_concepts/pygame_ce_rules_matches_2026-10-30.png`) ·
顺子与对子规则图 (仅本地: `docs/ui_concepts/pygame_ce_rules_combinations_2026-10-30.png`)。

特殊骰子使用流派配色和内嵌类型标记。铜、银、金通过金属边框、品质条、B/S/G 字母及一至三道刻痕区分。
魔鬼和天使的万能面使用各自头像，规则不变。
掷骰时播放简短的转动、弹跳动画；**Skip animation** 会立即展示同一个结果。
仅剩余可掷骰子参与动画，动画结束后才恢复游戏操作。播放或跳过动画消耗的游戏随机数完全一致。

**New Run** 先展示恶龙赌约插图和开局领取选择。
选择抽取会从 Lucky/Two/Odd/Even/Momentum 中不重复抽出三种 Bronze 骰子；
有 **20%** 概率将随机一颗替换成 **Silver Rescue**，否则三颗均为 Bronze。
每颗都可单独保留或放弃，不会随机抽空，也没有 Lucky Silver 分支；普通骰子仍保留。
当前开局三骰界面 (仅本地: `docs/ui_concepts/pygame_ce_initial_three_dice_2026-10-30.png`)。
**WARD** 是额外生命的故事名称：降到 0 仍可继续，而输给 Boss 无论剩余多少都会结束冒险。
开场图片随游戏提供，路径为 `assets/gui/dragon_wager_intro.png`；生成提示词和素材说明仅保留在本地开发目录。

赌注、奖励、合成、猜大小、转盘和商店均可用鼠标操作。
保留奖励前需要选择放置槽位；**Preview Merge** 仅预览合成，确认放置前不消耗材料。
赌注或商店中的 **Merge Dice** 可以免费合成两颗符合条件的已装备骰子，不占用商店付费服务。
双方在每场战斗中 Bank 或 Bust 后，都会显示结果 1 秒并自动继续，无需点击 Next Turn。
退出确认框会暂停自动继续。Hot Dice 后六颗已计分骰子保留在左侧，直到下一次投掷才返回中央。
普通骰子模式和装备骰子模式都会按预览中展示的实体骰子执行拿取。
对手会配合动作说简短台词，完整策略理由仍写入 `.txt` 日志；事件及五名对手也有简短故事文本。

猜大小使用实际骰子的投掷动画展示输赢；加权转盘减速后停在控制器已经选定的扇区。
两者都支持 **Skip animation**，结果保持到点击 **Continue** 为止，跳过动画不会改变事件概率。
击败 Boss 后至少提供一颗 **Gold** 奖励骰，即使此前选择现金或较低品质骰子下注也一样。
如果已赢得 Gold 赌注，就不重复发放；赌注仍按双方实际对应品质结算。

完成奖励选择后，结束故事和七项 **TOTAL SCORE** 在同一界面展示。公式 v1 为：

| 维度 | 得分 |
|---|---:|
| 剩余 WARD | 每个 500 |
| 获得金币 | 按获得数量计分 |
| 接收的特殊骰子 | Bronze/Silver/Gold 每颗 100/250/600 |
| 最高单回合入账 | 入账分数 ÷5，向下取整 |
| 最长成功入账连投 | 第一投之后，每次成功投掷 +50 |
| 单回合入账达到整场目标 | +1000 |
| 回合效率 | `max(0, 500 × 获胜场数 − 20 × 双方总回合数)` |

金币收入不包括初始 100 金币、退回的本金和退款。Bust 的回合不计入成功入账记录。
现有 UTF-8 日志保存明细、总分和结构化计分历史，可以重放同一计算。
这些表现分权重是临时方案，并未调整战斗难度。

**Leaderboard** 从本地 `match_logs/*.txt` 读取已结束且采用公式 v1 的冒险记录，每页显示八条。
胜利与失败记录均参与排名，先按总分降序，同分时较新的记录优先。
退出、未完成、损坏或没有分数的旧日志不参与排名。每次进入都会重新读取，不修改日志，也不生成第二份索引。
当前排行榜界面 (仅本地: `docs/ui_concepts/pygame_ce_local_leaderboard_2026-10-30.png`)。

成长奖励、对手装备和商店还可以出现两种骰面公平的效果骰子：

- **Momentum**（紫色 / M，蓄势）：合法计分时，本回合此前每次成功计分选择提供 +100，
  每次选择最多 +400；同时选中多颗 Momentum 只共享一份加分。
  Hot Dice 恢复骰子并保留累计次数，Bank/Bust 清零。这是尚未平衡的临时数值。
- **Rescue**（灰蓝色 / R，救援）：实体骰子仍可掷时，可选择重掷整个剩余骰池，每场战斗一次。
  无法计分时会在清空风险分前提供 **Use rescue** 或 **Accept Bust**。
  每方最多装备一颗，新战斗恢复次数；所有来源固定 **Silver**，不能合成或升级，但并非全局唯一。
  CLI 在确认选择前或救援提示中输入 `R` 使用，`S` 接受 Bust。

Momentum 当前铜、银、金效果相同。特定组合加分和一次性爆发骰子仍未实现。

AI 默认每个动作停顿两秒，方便观察。快速测试可以使用：

```powershell
.\.venv\Scripts\python.exe main.py --gui --ai-delay 0
```

**Exit run**、Escape 或关闭窗口会打开确认框，默认聚焦 **Keep playing**，Escape 取消退出。
AI 在确认框后继续行动。**End run** 等待赌注退款和日志关闭完成后再返回主菜单或退出窗口。
当前没有中途保存/恢复。实际窗口冒险与 CLI 共用时间戳 UTF-8 日志，自动实验不生成个人记录。
调整窗口大小会保持比例、映射鼠标坐标，最小窗口为 960×600，多余区域留边。

已保存实际渲染的 V3 主菜单 (仅本地: `docs/ui_concepts/pygame_ce_v3_menu_implemented.png`)、
战斗 (仅本地: `docs/ui_concepts/pygame_ce_v3_battle_implemented.png`)、
Roll/Bank (仅本地: `docs/ui_concepts/pygame_ce_v3_decision_implemented.png`) 和
退出确认 (仅本地: `docs/ui_concepts/pygame_ce_v3_exit_implemented.png`) 截图。
此前桌面锁定限制了人工点击检查；自动鼠标和键盘测试覆盖完整成长流程、确认退出，以及
960×600、1280×800、1600×900、1920×1080 和 2560×1080 的点击坐标。

10 月 29 日的插图与皮肤示例包括开场 (仅本地: `docs/ui_concepts/pygame_ce_opening_2026-10-29.png`)、
战斗骰子 (仅本地: `docs/ui_concepts/pygame_ce_dice_2026-10-29.png`)、
骰子目录 (仅本地: `docs/ui_concepts/pygame_ce_dice_catalog_2026-10-29.png`)、
自动 Bust (仅本地: `docs/ui_concepts/pygame_ce_bust_auto_2026-10-29.png`)、
AI 对话 (仅本地: `docs/ui_concepts/pygame_ce_ai_dialogue_2026-10-29.png`)、
Rescue (仅本地: `docs/ui_concepts/pygame_ce_rescue_2026-10-29.png`) 和
Momentum 预览 (仅本地: `docs/ui_concepts/pygame_ce_momentum_2026-10-29.png`)。
另有菜单 (仅本地: `docs/ui_concepts/pygame_ce_menu_2026-10-29.png`)、
猜大小结果 (仅本地: `docs/ui_concepts/pygame_ce_guess_result_2026-10-29.png`)、
转盘结果 (仅本地: `docs/ui_concepts/pygame_ce_spinner_result_2026-10-29.png`) 和
最终结算 (仅本地: `docs/ui_concepts/pygame_ce_run_score_2026-10-29.png`)。

## 项目状态

已实现并测试规则核心与固定五场玩家对 AI 冒险。
GUI 和 CLI 共用计分、选择验证、Bust、Bank、Hot Dice 和成长流程。
冒险包含一条额外生命、赌注、胜利金币、事件、奖励和商店。

另有无界面 AI 对战模拟器。Normal 的保守、中性、激进和复合人格可用于游戏及模拟，
Hard 暂停开发，第一场对手为 Easy。

当前计分规则包括三个 1 为 500 分，三颗之后每增加一颗同点骰 +200，顺子为 500/600/1200 分，
以及普通三对、连续三对、重复 Hot Dice 和合法零分动作。
每场战斗由玩家和 AI 交替行动，一方入账达到 2000 分立即获胜。
每场重置双方分数，装备和金币跨场保留；待处理的平衡工作见 TODO.md (仅本地: `TODO.md`)。

成长与事件可通过 `--run` 游玩，参见
game_rules 第 8 节 (仅本地: `docs/game_rules.md#8-已确认的成长与事件规则`)、
游戏流程 (仅本地: `docs/游戏流程.md`)、骰子规则 (仅本地: `docs/骰子规则.md`)。
事件顺序为第 1 场后猜大小、第 3 场后转盘、第 4 场后商店。
骰子效果设计分析 (仅本地: `docs/骰子效果设计分析.md`) 保留效果与套装候选方案，遗物和套装加成尚未实现。
较早的经济实验 (仅本地: `docs/数值与事件分析.md`)及 `python tools/economy_analysis.py`
对应旧版五项转盘、不受品质限制的模型，并不代表最新规则，也不能衡量特殊骰子战斗或当前 AI 强度。

CLI Gamebar 展示回合、阶段、已入账分数和目标、风险分、最新骰子、选择位置、剩余骰子、命令及结果。
交互终端原地刷新，重定向和自动测试保留可读文本帧。
计分规则独立置于 Gamebar 上方，两框均宽 66 列，可放入常见的 80 列终端，避免旧版左右并排导致的换行。

## 基础规则

- 每场战斗前公平掷一次 0/1：0 表示 AI 先手，1 表示玩家先手。
  结果持续显示，不参与计分，回合间不重复掷。
- 玩家和对手交替行动，每个回合从六颗骰子开始。
- 每次投掷后选择一个合法得分子集；也可明确使用普通三对，以 +0 重掷六颗并保留此前风险分。
- 所选分数加入本回合未入账分数。
- 可以 Bank 收手入账并结束回合，或继续掷剩余骰子，冒险争取更多分数。
- 若既无正分选择，也无普通三对动作，则 Bust，本回合全部未入账分数丢失。
- 已入账分数安全保留，必须通过入账达到目标才算赢；默认目标为 2000 分。
- Hot Dice 已启用：本回合六颗骰子全部计分后，恢复六颗可掷骰子，累计风险分保留。

### 基础计分

| 骰子或组合 | 分数 |
|---|---:|
| 单颗 1 | 100 |
| 单颗 5 | 50 |
| 三个 1 | 500 |
| 三个 2 | 200 |
| 三个 3 | 300 |
| 三个 4 | 400 |
| 三个 5 | 500 |
| 三个 6 | 600 |

三颗之后每增加一颗同点骰 +200；顺子为 500/600/1200 分。
普通三对可 +0 重掷；连续三对 112233/223344/334455/445566 分别为 1200/1000/1100/1200 分，
并触发 Hot Dice。两组三同将各自分数相加，没有额外奖励。
完整计分表、选择规则和例子见 docs/game_rules.md (仅本地: `docs/game_rules.md`)。

## 冒险结构

运行 `python main.py --run` 可挑战以下固定顺序：

1. 普通敌人：Easy，收手阈值 500，尚未平衡。
2. 普通敌人：Normal 保守人格。
3. 普通敌人：Normal 激进人格。
4. 精英敌人：Normal 中性人格。
5. Boss：Normal 复合人格，并非 Hard。

初始持有 100 金币和六颗普通骰子。第一场前可参与开局领取；第一场后猜大小，第三场后六项转盘，第四场后商店。
五场获胜的固定金币奖励为 200/200/250/350/500，失败不发放。对手人格固定，装备按场次生成。

HP 表示额外生命，初始为 1。前四场中，HP=1 时失败会消耗它，以 HP=0 进入下一场，而非重试当前战斗。
HP=0 本身仍可游玩，但再次失败就结束；输给 Boss 无论剩余多少额外生命都会结束，击败 Boss 则获胜。
每场双方分数归零，回合状态重置，重新掷 0/1 决定先手；HP、金币和玩家装备跨场保留。
CLI 场间按 Enter 前进，Q/EOF/Ctrl-C 退出不会额外扣命；退出时未结算的现金赌注会退款。

### 游玩成长版本

```powershell
python main.py --run
python main.py --run --ai-delay 0
python main.py --run --ascii
```

默认 AI 每步停顿两秒。字体不能正确显示花色时可使用 `--ascii`，输出编码不支持时也会自动回退。

| 界面 | CLI 命令 |
|---|---|
| 开局领取 | Enter/P 抽取，S 跳过 |
| 赌注 | `C 50` 赌现金；Enter 赌 0；`D 2` 用槽位 2 的骰子按实际对应品质下注 |
| 选择骰子 | 输入当前可选的固定槽位，例如 `1 3 5` |
| 选择之后 | R 继续掷，B 入账 |
| 查看信息 | H 帮助；`I 3` 查看行动方槽位；`I other 3` 查看对方槽位 |
| 接收骰子 | `1..6` 替换槽位；`M 2` 预览与槽位 2 合成；D 放弃/取消 |
| 已装备合成 | 赌注/商店输入 `M 1 2` 免费合成符合条件的骰子，结果放槽位 2 |
| 猜大小 | Enter/P 参与；S 小、B 大；赢后 B 领取或 R 继续冒险 |
| 转盘 | Enter/P 转动，S 停止；最多不放回抽取三次 |
| 商店 | `buy 2`、`upgrade 3`、`remove 3`、`refresh`、Enter/leave |

Q 退出。只有战斗新赢得的骰子可以放弃并折现原价的 80%，初始和事件骰子不返现金。
取消合成预览保留材料。商店仅提供一次付费升级/移除和一次刷新，免费合成不占用服务。

| 骰子 | 符号 / ASCII | 效果 |
|---|---|---|
| Lucky | ♣ / L | 偏置 1、6 |
| Two | ♦ / T | 偏置 2 |
| Odd | ▲ / O | 偏置 1、3、5 |
| Even | ■ / E | 偏置 2、4、6 |
| Devil | ♠ / D | 自然 1 替换为万能面 `*` |
| Angel | ♥ / A | 自然 5 替换为万能面 `*` |

B/S/G 表示品质，偏置骰面在三个品质的权重为 2/3/4，其余面权重为 1。
Devil 和 Angel 固定 Silver、不能升级，整个冒险中每种最多生成一次，涵盖 AI 和未购买的商店库存。
它们没有使用次数限制。万能面只能补成 3–6 颗同点组合或 5–6 颗顺子，不能单颗计分或组成三对。
所选子集采用合法替代中的最高分，并在 Gamebar 和日志中展示。物品处理细则见骰子规则 (仅本地: `docs/骰子规则.md`)。

## 对手策略

Easy 按收手阈值决定是否继续：低于阈值继续，达到阈值收手。
**Hot Dice** 是例外：即使已达到阈值，也先再掷六颗，直到下一个非 Hot Dice 的正分决策再判断阈值；
每次新的 Hot Dice 都重复该规则。若立即 Bank 就能获胜，则始终优先获胜。
CLI、GUI 和无界面对战共用该判断，Normal 人格不受此次例外调整影响。

Easy 选择即时分数最高的合法动作；同分时选择升序位置元组中字典序最早者。
默认阈值 500 是测试起点，不是最终平衡值。骰子、选择、得分、Hot Dice 和 Bank/Roll 理由按顺序展示，
CLI 每步停顿两秒，完整回合后按 Enter 前进。AI 播放期间 Ctrl-C 退出不会把风险分入账。

Normal 使用回合效用策略，Hard 胜率模型暂停开发。
特殊装备的 Normal 根据真实加权概率，向前观察一次未来正分投掷，并在每次决策时重新规划；
普通骰子的完整回合计算表保持原实现。早期普通骰子胜率报告不能证明特殊骰子的实际强度，
当前模型不是胜率求解器。AI 决策保持确定性，不使用机器学习。

## 已实现与暂缓功能

- 已实现持续刷新的 ASCII Gamebar 和可选鼠标界面。
- 已实现五名具有不同风险偏好的对手。
- 已实现金币、特殊骰子、单个商店和胜败结算。
- 已有输入验证，以及计分和状态变化的自动测试。
- 遗物、更多效果和套装加成仍处于设计阶段。
- 当前商店规则不包含治疗。

Version 1 不包含多人联机、地图探索、跨局永久成长或大型背包系统。

## 环境要求

- 推荐 Python 3.10 或更新版本。
- 命令行版本和无界面模拟器只使用标准库。
- 可选窗口界面需要 `pygame-ce==2.5.8`，见 [requirements-gui.txt](requirements-gui.txt)。

## CLI 冒险参数

开始完整五场冒险，初始有一条额外生命：

```powershell
python main.py --run
```

取消 AI 阅读停顿，或改用字母标记：

```powershell
python main.py --run --ai-delay 0
python main.py --run --ascii
```

Normal 考虑剩余骰子并比较期望回合效用，不使用 Easy 收手阈值。
保守/中性/激进的 gamma 为 0.5/1/2；复合人格按分差和对手威胁在回合开始选择人格，整回合保持。
Normal 的理由和效用会展示并记录，但效用不是胜率。
`--ambition` 只影响 Easy，提供时仍须为正整数；`--ai-delay` 对两类 AI 都有效。
冒险的场次人格固定，不能覆盖。

`--ai-delay 0` 只取消定时停顿，CLI 的完整回合后仍需 Enter。延迟必须为有限非负数。
输入 `1 3 5` 等位置选择骰子，然后 `R` 继续或 `B` 入账；完整回合后 Enter 继续，Q 退出。
普通三对必须明确选择六颗才能 +0 重掷，重掷前不会出现 Bank 提示，但也可只选其中可计分的 1/5。
Q、EOF 或 Ctrl-C 退出当前冒险。

`models.MatchState` 管理双方分数、行动方和胜者；`ui.py` 仅展示和解析输入，计分与状态变化留在核心模块。
`progression.run_campaign()` 在 `models.RunState` 上协调场次和额外生命，每场复用 `battle.run_match()`。

## 对局记录

实际 GUI/CLI 冒险会自动保存为 `match_logs/` 中的 UTF-8 文本文件，按本地开始时间命名，
例如 `2026-10-08_15-30-20_123456.txt`。微秒区分同秒启动，已有记录不会覆盖。
CLI 会在结束或退出后输出保存路径。

每个事件包含回合、行动方、按位置排列的骰面、选择位置、剩余骰子、阶段、双方已入账分数、
行动方当前分数和未入账分数，还记录 AI 收手/继续理由、Hot Dice、普通三对、Bust 损失、胜者和提前退出。
每次事件立即刷新文件，意外中断前的动作可保留；退出时丢弃风险分，不自动入账。

一整次冒险保存在同一个时间戳文件中，包含 RUN/STAGE 开始与结束事件，以及每次动作的场次和 HP 上下文。
每场分数独立，不会跨场继承。未传入日志写入器的直接控制器调用（包括自动测试/模拟）不生成个人记录。
日志测试使用临时目录。记录仅保存在本地，已被 Git 忽略，没有上传或自动删除。

## 无界面 AI 对战实验

默认运行 100 场 Easy 500 对 Easy 500：

```powershell
python -m the_kings_gambit.simulation --games 100 --seed 20261013
```

比较不同 Easy 阈值：

```powershell
python -m the_kings_gambit.simulation --games 100 --ambition-a 500 --ambition-b 750 --seed 20261013
```

用 `--ai-a` / `--ai-b` 指定双方人格：

```powershell
python -m the_kings_gambit.simulation --games 100 --ai-a composite --ai-b easy --seed 20261013
python -m the_kings_gambit.simulation --games 100 --ai-a conservative --ai-b aggressive --seed 20261013
```

默认目标 2000，可用 `--target` 调整。场数、阈值和目标须为正整数，种子为整数。
每场分数归零，入账达到目标立即停止。A/B 轮流先手，100 场各先手 50 次，奇数场 A 多一次。
第 i 场使用 seed+i。这只用于实验，实际游戏保留随机 0/1 先手。
不同策略消耗随机数的数量不同，同种子并不代表每回合会拿到相同骰面。

报告包含胜场、近似 95% Wilson 区间、先/后手胜场、回合数、投掷数、Bust 率、
每次成功 Bank 平均分、Hot Dice、普通三对和总耗时。除耗时外，核心实验可复现。
实验不显示 UI、不读输入、不停顿、不写文件，也不使用个人 `match_logs/`；触发安全限制会明确报错，不伪造平局。

100 场实验独立于 unittest，仅为初步样本，不能证明某个阈值最优。
参见 Normal 实现 (仅本地: `docs/normal_ai_design.md`)、Normal 初步结果 (仅本地: `docs/normal_ai_results.txt`)
和 10 月 13 日 Easy 基线实验 (仅本地: `docs/ai_simulation_baseline.txt`)，这些报告没有改变默认阈值 500。

运行 Easy 500 与四种 Normal 人格的全部两两组合：

```powershell
python -m the_kings_gambit.simulation --round-robin --games 1000 --seed 2026102600
```

此时 `--games` 指每组场数，五种策略共十组、合计 10000 场。
每组使用 `seed + pair_index * games` 起始的独立种子区间，要求场数为偶数，以保证双方先手次数相等。
循环赛默认种子为 2026102600，与双边实验默认的 20261013 不同；组合顺序按 `ai.py` 的 `AI_TYPES`。
Easy 固定阈值 500，不接受冲突的双边 AI/阈值参数。

循环赛输出胜率矩阵、总体汇总和各组报告，不自动调参，也不写文件。
这些是实验对局胜率，不是 Normal 决策效用，也不能保证关卡难度递增。
大实验结束后统一输出；当前环境一次 10000 场约四分钟，不代表所有电脑的固定耗时。
参见 10 月 26 日交叉对战结果 (仅本地: `docs/ai_round_robin_2026-10-26.txt`)。

## 运行测试

`tests/` 目录仅保留在本地，不包含在公开的运行文件中；以下命令用于完整开发目录。

```powershell
python -m unittest discover -s tests
```

安装 GUI 依赖后，使用同一环境运行，才能包含窗口渲染和鼠标测试。Windows：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

macOS/Linux：

```bash
./.venv/bin/python -m unittest discover -s tests
```

未安装 pygame-ce 时，可选渲染测试跳过，核心和桥接测试仍会运行。
GUI 测试使用离屏 SDL、注入骰子结果和临时日志，不写入个人 `match_logs/`。

## 本地开发文档

- 游戏设计 (仅本地: `docs/game_design.md`)：概念、范围、流程、界面与完成标准。
- 游戏规则 (仅本地: `docs/game_rules.md`)：精确计分和回合规则。
- 计分与 AI 历史参考 (仅本地: `docs/scoring_and_ai_reference.md`)：归档来源，统计结论仍需独立复现。
- Normal AI 设计 (仅本地: `docs/normal_ai_design.md`)：三种固定人格与情境式复合人格，Hard 暂停。
- Hard AI 备忘录 (仅本地: `docs/hard_ai_memo.md`)：离线胜率模型想法，并非实现要求或当前 Boss 策略。
- 待办事项 (仅本地: `TODO.md`)：未决设计和开发工作。
- 开发约束 (仅本地: `AGENTS.md`)：模块边界与质量要求。

## 完整本地项目结构

```text
README.md                       # 英文说明
README.zh-CN.md                 # 简体中文说明
requirements-gui.txt            # 可选 pygame-ce 依赖
main.py                         # 命令行/窗口启动入口
the_kings_gambit/
|-- main.py                      # 参数解析与个人日志
|-- dice.py                      # 实体骰子与加权投掷
|-- scoring.py                   # 合法子集与万能面替代
|-- models.py                    # 物品、回合、战斗与冒险状态
|-- battle.py                    # 共用玩家/AI 回合流程
|-- ai.py                        # Normal 效用与人格
|-- simulation.py                # 无界面普通骰子 AI 实验
|-- progression.py               # 赌注、奖励、事件、商店与五场流程
|-- run_score.py                 # 可重放的七项冒险评分，不做 I/O
|-- gui_session.py               # 工作线程、隔离快照与输入请求
|-- gui.py                       # pygame-ce 绘制与鼠标交互
`-- ui.py                        # 文本面板、符号与输入
tests/                          # unittest，不生成个人对局记录
|-- test_dice.py
|-- test_scoring.py
|-- test_ai.py
|-- test_normal_ai.py
|-- test_simulation.py
|-- test_progression.py
|-- test_growth.py               # 经济系统与完整成长冒险
|-- test_gui.py                  # 快照隔离与完整鼠标流程
|-- test_special_dice.py         # 权重、万能面、固定槽位与 AI
|-- test_effect_dice.py          # Momentum、Rescue、AI/成长/日志
|-- test_event_screens.py        # 事件动画与结果快照
|-- test_run_score.py            # 评分重放、收入与 Boss 奖励
|-- test_leaderboard.py          # 只读排行榜与损坏日志
|-- test_initial_rewards.py      # 开局三骰与固定 Silver Rescue
|-- test_match_log.py
|-- test_economy_analysis.py
`-- test_ui.py
docs/                           # 规则、设计与历史实验
assets/gui/                     # 开场插图及来源说明
match_logs/                     # 仅实际 GUI/CLI 对局
tools/                          # 历史经济分析工具
```

Review 建议从 `models.Die` 和 `dice.roll_item` 开始，再看 `scoring.turn_actions`、
`battle.begin_roll` / `resolve_roll`，最后看 `progression.run_campaign`。
界面负责展示状态，计分模块不做输入输出。
