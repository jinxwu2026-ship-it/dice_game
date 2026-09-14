---
name: beginner-python-code-review
description: Review beginner-level Python student projects in quick-review or final-audit mode for course suitability, explainability, correctness, project-rule compliance, and test coverage. Use when the user asks for a code review, lesson-scope check, or submission audit; do not use for ordinary implementation work.
---

# Beginner Python Code Review

Review student Python code without changing it. Optimize for code the student can understand, explain, test, and present, rather than for professional-level abstraction.

## Authority and context

Use sources in this order:

1. The user's current instructions.
2. The nearest applicable `AGENTS.md` files.
3. The project's rule, design, assignment, and task documents.
4. [The provisional COMP9001 baseline](references/comp9001-baseline.md).

Do not invent requirements from a missing rubric or assume that every introductory course labels topics the same way. Distinguish a confirmed prohibition from an unverified or unnecessarily advanced technique.

## Review-only boundary

A review request authorizes inspection, non-destructive diagnostics, and relevant test commands. It does not authorize edits to code, tests, documentation, configuration, or saved data.

- Report proposed replacements separately from the existing code.
- Do not apply a replacement until the user explicitly approves the named finding or clearly specified change.
- Treat approval as limited to the identified findings. Do not repair unrelated findings in the same edit.
- After an approved edit, run proportionate tests when permitted and report the result.

## Choose a mode

### Quick review

Use when the user names a file, feature, diff, or recent change, or explicitly requests `quick_review`.

- Inspect only the requested area and the minimum dependencies needed to judge it.
- If the target is recent work but no files are named, inspect the working-tree diff first.
- Prioritize correctness, project rules, beginner explainability, input validation, and directly relevant tests.
- Do not turn a focused review into a repository-wide audit.

### Final audit

Use when the user explicitly requests `final_audit`, a full-project review, or submission readiness.

- Inspect the whole submitted project, including code, tests, run instructions, documentation, and relevant design artifacts.
- Follow the project's documented run and test commands. For this project, prefer the standard-library `unittest` command specified by `AGENTS.md` when it exists.
- Check that the tutor can run the program without unexplained setup or unavailable dependencies.
- Verify required behavior against the project's sources of truth and connect test evidence to important state transitions.
- Identify at least two clearly demonstrated course topics without overstating uncertain classifications.
- Review any required flowchart as design evidence, not as executable code.
- Give a readiness verdict, but do not predict a mark while the detailed rubric is unavailable.

## Beginner-level review policy

- Prefer small functions, explicit control flow, and ordinary lists and dictionaries.
- Simple classes are acceptable when they make state clearer, but flag classes, inheritance, or patterns that add complexity without a concrete benefit. Do not demand a rewrite merely because a class exists.
- Type hints are optional and unnecessary for this project. Do not recommend adding them; mention existing annotations only if they harm readability or conflict with course expectations.
- Accept Python standard-library modules when their purpose is understandable.
- Flag third-party dependencies when they are unnecessary, difficult to package, or inconsistent with project instructions.
- Treat decorators, metaclasses, asynchronous code, complex inheritance, and sophisticated design patterns as unverified techniques. Explain the concern and suggest a simpler approach instead of claiming they are forbidden without evidence.
- Judge explainability directly: could the student describe the purpose, inputs, outputs, and state changes of this code in plain English?

## Course evidence for this project

Treat file I/O and program design as intended course evidence.

- Settings, match history, and rankings should use simple local persistence such as JSON or CSV when the project requires them.
- Rankings must remain local: no networking, accounts, or online leaderboard.
- Saved records must not create permanent gameplay upgrades or contradict the project's no-permanent-progression rule.
- A ranking may be calculated from match-history data instead of duplicating the same information in another store.
- Do not force persistence into scoring or battle logic when it belongs in a separate storage or progression boundary.

The absence of settings, history, rankings, or a flowchart is a blocker only if current project or assignment instructions make it required. Otherwise describe it as missing planned course evidence or a suggestion, as appropriate.

## Findings

Use these levels:

- `BLOCKER`: broken required behavior, crash, failed required test, rule violation, missing required feature, or inability to run the submission.
- `IMPORTANT`: meaningful correctness risk, unclear state handling, missing validation, poor separation, insufficient testing, or code the student is unlikely to explain confidently.
- `SUGGESTION`: a non-essential simplification or readability improvement.
- `GOOD EVIDENCE`: a concrete, defensible example of a course concept or sound problem-solving choice.

For each problem, include:

1. A stable finding ID such as `B1`, `I1`, or `S1`.
2. The level and a concise title.
3. A clickable file and line reference when available.
4. What the code currently does.
5. Why it matters under a named project or course source.
6. The smallest beginner-appropriate recommendation.
7. A proposed replacement snippet only when it materially clarifies the fix.

Order findings by severity, then by execution flow. Avoid style comments that have no effect on understanding, correctness, assessment evidence, or maintenance.

## Report shape

Lead with the outcome.

For a quick review, report the reviewed scope, findings, relevant test evidence, and a short conclusion.

For a final audit, report:

- readiness verdict;
- blockers and important findings;
- test and run evidence;
- requirement coverage;
- demonstrated course topics;
- unnecessary or unverified complexity;
- tutor run-readiness; and
- suggestions and good evidence.

If no problems are found, say so directly and identify remaining limits in what was inspected or executed.
