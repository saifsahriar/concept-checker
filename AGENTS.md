## Plan & Review

### Before starting work
- Start every new task in **Plan mode** (`/plan` or Shift+Tab to cycle into Plan). Do not switch to Pair/Execute mode until a plan exists and is approved.
- Plan mode does not hard-block file edits at the runtime level — it's a self-imposed discipline. Do not write or modify any files while in this phase, even if a tool technically allows it.
- Write the plan to `.codex/tasks/TASK_NAME.md`.
- The plan must be a detailed implementation plan with reasoning behind each decision, broken into discrete tasks.
- If the task touches an unfamiliar package, API, or library, research current docs/usage before finalizing the plan (web search if available) — don't guess at APIs from training data.
- Don't over-plan. Always default to the smallest MVP version of the task.
- Once `.codex/tasks/TASK_NAME.md` is written, stop and ask for review. Do not proceed to Pair/Execute mode until the plan is explicitly approved.

### While implementing
- Update `.codex/tasks/TASK_NAME.md` as work progresses — keep it in sync with reality, not just the original plan.
- After finishing each task, append a detailed changelog entry to the same file describing exactly what changed and why, so the task can be picked up by another engineer (or a future Codex session) with no extra context needed.