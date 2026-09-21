# AGENTS.md — qtframeless

---

## Available Skills

Use these specialized skills for detailed patterns and strict project conventions:

| Skill | Description | Location |
| --- | --- | --- |
| `numpy-docstrings` | Strict NumPy-style docstrings and human-sounding comments | [.agents/skills/numpy-docstrings/SKILL.md](.agents/skills/numpy-docstrings/SKILL.md) |
| `naming-conventions` | Strict camelCase/PascalCase naming, no abbreviations, Qt properties/signals/slots | [.agents/skills/naming-conventions/SKILL.md](.agents/skills/naming-conventions/SKILL.md) |
| `commit-hygiene` | Conventional Commits, project-specific scopes, and atomic Git history | [.agents/skills/commit-hygiene/SKILL.md](.agents/skills/commit-hygiene/SKILL.md) |
| `qt-testing` | Reliable UI & widget tests with pytest-qt, qtbot, signals, and no sleeps | [.agents/skills/qt-testing/SKILL.md](.agents/skills/qt-testing/SKILL.md) |
| `grill-me` | Interview a loose idea until it hardens into decisions — stateless, no repo required | [.agents/skills/grill-me/SKILL.md](.agents/skills/grill-me/SKILL.md) |
| `grill-with-docs` | Interview a change inside a repo; writes `CONTEXT.md` and ADRs as vocabulary settles | [.agents/skills/grill-with-docs/SKILL.md](.agents/skills/grill-with-docs/SKILL.md) |
| `systematic-debugging` | Root cause investigation before any fix — Iron Law, four phases, Qt/pytest-qt instrumentation | [.agents/skills/systematic-debugging/SKILL.md](.agents/skills/systematic-debugging/SKILL.md) |
| `codebase-design` | Design deep modules with high leverage, clean seams, and Design It Twice | [.agents/skills/codebase-design/SKILL.md](.agents/skills/codebase-design/SKILL.md) |
| `release-notes` | Comprehensive release notes, changelog updates, version tagging, and GitHub Releases | [.agents/skills/release-notes/SKILL.md](.agents/skills/release-notes/SKILL.md) |

---

## Auto-invoke Trigger Matrix

When performing any of these actions, **ALWAYS invoke the corresponding skill FIRST**:

| Action / Intent | Required Skill |
| --- | --- |
| Writing or modifying public modules, classes, functions, or methods | `numpy-docstrings` |
| Writing inline code comments or documenting architectural decisions | `numpy-docstrings` |
| Declaring or renaming functions, methods, variables, or parameters | `naming-conventions` |
| Declaring or refactoring Qt signals, slots, or event handlers | `naming-conventions` |
| Implementing Qt properties (`Property(...)`), getters, or setters | `naming-conventions` |
| Defining enum classes, enum members, or global constants | `naming-conventions` |
| Reviewing code for naming consistency or abbreviation violations | `naming-conventions` |
| Writing, updating, fixing, or debugging Qt widget tests or signals | `qt-testing` |
| Creating, reviewing, drafting, or staging Git commits | `commit-hygiene` |
| Creating, drafting, or publishing release notes, changelogs, version tags, or GitHub Releases | `release-notes` |
| User describes a loose idea, feature direction, or change before any spec exists (no repo context needed) | `grill-me` |
| Starting `sdd-propose` Step 0 with fuzzy intent or unsettled vocabulary inside this repo | `grill-with-docs` |
| User says "tengo una idea", "quiero agregar X", "pensé en cambiar Y" without a clear spec | `grill-me` |
| User invokes any `/sdd-*` command and intent or scope is still fuzzy or vocabulary is unsettled | `grill-with-docs` — MUST complete before delegating to SDD, regardless of mode (interactive or automatic) |
| User invokes any `/sdd-*` command and key domain terms are ambiguous or contradictory | `grill-with-docs` — settle vocabulary in `CONTEXT.md` first, then proceed to the requested SDD phase |
| User invokes any `/sdd-*` command with no existing spec and no prior grilling session in this conversation | `grill-with-docs` — do NOT skip this even in automatic mode unless the user explicitly says "skip grilling" |
| Encountering any bug, test failure, pytest error, Qt crash, flaky test, or unexpected behavior | `systematic-debugging` — MUST run Phase 1 before any fix is proposed |
| Designing new modules, refactoring shallow interfaces, or executing `sdd-design` | `codebase-design` — MUST formulate at least two alternative interfaces |
