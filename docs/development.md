# Development workflow / 开发流程

## Rule revision workflow / 规则修订流程

用户当前指示 → `game_rules.md`（精确规则）→ `game_design.md`（范围与设计）
→ `TODO.md`（迁移与未决事项）→ 实现与测试。`AGENTS.md` 和 README 同步摘要。
归档材料 `scoring_and_ai_reference.md` 用于追溯，不覆盖上述规范。

2026-09-21 已将新版计分、合法 +0 动作、Bust、回合状态与 UI 提示迁移到单人练习，
同步更新测试；Bank 总分达到 2,000 时结束练习。本阶段明确不包含 AI。
五关、对手、奖励、HP 和完整 gamebar 等后续工作按 TODO 推进。
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
