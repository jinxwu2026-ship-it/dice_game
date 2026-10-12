# Development workflow / 开发流程

## Rule revision workflow / 规则修订流程

用户当前指示 → `game_rules.md`（精确规则）→ `game_design.md`（范围与设计）
→ `TODO.md`（迁移与未决事项）→ 实现与测试。`AGENTS.md` 和 README 同步摘要。
归档材料 `scoring_and_ai_reference.md` 用于追溯，不覆盖上述规范。

2026-09-21 已将新版计分、合法 +0 动作、Bust、回合状态与 UI 提示迁移到单人练习，
同步更新测试；Bank 总分达到 2,000 时结束练习。当时的单人练习阶段不包含 AI。
2026-10-06 已将练习流程协调移入 `battle.run_practice()`；`ui.py` 负责输入解析与
ASCII gamebar 渲染。交互终端清屏刷新，测试或重定向输出保留文本帧。
gamebar 显示回合、阶段、目标、Bank 分数、风险分、当前骰子、所选位置、
可用骰子数量、命令与结果，覆盖 Bust、Bank、Hot Dice、普通三对和胜利。
2026-10-07 按用户要求实现单场 Player 对 Easy AI：共享选骰和回合规则，最高即时分
优先，同分采用最早位置元组；能赢立即 Bank，否则按默认 500 的 ambition 判断。
AI 掷骰、选骰和 Bank/Roll 理由逐步展示，默认每步 2 秒，结束回合后 Enter 换手。
`python main.py` 启动对局；`--practice` 保留练习；`--ai-delay` 和 `--ambition` 可调整。
测试注入骰子和暂停函数，不依赖真实等待。五关、奖励、HP 和成长区域按 TODO 推进。
2026-10-08 新增开场 0/1 掷骰：`dice.roll_first_turn()` 只生成结果，`battle.py`
在首回合前按 0 = AI / 1 = 玩家设置先手，并将提示传给 gamebar 持续显示。
开场结果保存在 `MatchState.starting_roll`；练习不掷，之后各回合仅正常换手。
同日加入对局记录：`battle.run_match(log_func=...)` 发送逐事件文本，`main.py`
为实际 CLI 对局创建 `match_logs/开局时间.txt`，UTF-8、每条刷新、拒绝覆盖旧文件。
记录双方骰子、选择、AI 理由及分数状态；退出也保留已有内容。核心默认不提供
writer，测试及模拟不会生成个人日志；文件测试使用项目内自动清理的临时目录。
新规则验收清单在 `game_rules.md` 第 6 节；统计复现不作为独立基础开发的阻塞项。

运行全套测试：`python -m unittest discover -s tests`。
测试通过不等于设计迁移完成，应同时检查新规则对应测试是否已补齐。
下图中的 commit / push 是后续人工选择的步骤，本次文档任务不自动提交或推送。

## Existing workflow / 原工作流

```text
              ┌──────────────┐
              │ game_design  │
              │     .md      │
              └──────┬───────┘
                     ↓
              ┌──────────────┐
              │    Codex     │
              │     CLI      │
              └──────┬───────┘
                     ↓
AGENTS.md ───→ Python Code ←── Skills
                     ↓
                 Run/Test
                     ↓
                  git diff
                     ↓
                  commit
                     ↓
                   push
                     ↓
                  GitHub
```
