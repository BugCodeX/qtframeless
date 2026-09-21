---
name: commit-hygiene
description: "Trigger: commit, git commit, commit message, commit hygiene, conventional commits, historial git. Enforce clean Conventional Commits and atomic Git history for QtMaterial3."
license: MIT
metadata:
  author: BugCodeX
  version: "1.0"
---

# Skill: commit-hygiene

## Purpose

Enforce Conventional Commits, atomic changes, and a clean, readable Git history tailored specifically for the **QtMaterial3** monorepo workspace.

## When to Use

Any time a Git commit is created, reviewed, staged, or suggested.

## Format

```text
type(scope): description
```

Validated by regex:

```regex
^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)(\([a-z0-9\._-]+\))?!?: .+
```

## Valid Types

| Type | Use For |
| --- | --- |
| `feat` | New component, property editor, or library behavior |
| `fix` | Bug fix in rendering, properties, plugins, or logic |
| `docs` | Documentation only (READMEs, docstrings, architecture guides) |
| `chore` | Maintenance, dependency updates, packaging setup |
| `refactor` | Code restructuring without logic or visual behavior change |
| `test` | Adding, updating, or fixing tests |
| `ci` | GitHub Actions or automated workflow changes |
| `style` | Formatting, whitespace, linter fixes with no logic change |
| `perf` | Rendering performance or caching optimizations |
| `build` | Build system, Makefile, uv workspace, or pyproject.toml changes |
| `revert` | Reverting a previous commit |

## Valid Scopes for QtMaterial3

| Scope | Covers |
| --- | --- |
| `core` | Core mixins (`M3IconWidgetMixin`, `M3ThemeWidgetMixin`, `M3ElevationMixin`, etc.) |
| `buttons` | `Button`, `IconButton`, `HyperlinkButton`, `SegmentedButton` |
| `containers` | `Card`, `TextCard`, `ImageCard`, `ActionCard` |
| `icons` | Material Symbols font loader, registry, ligature engine, and icon catalog |
| `text` | M3 Typography labels (`LabelDisplay`, `LabelHeadline`, `LabelBody`, etc.) |
| `theme` | `ThemeManager`, `ThemeMode`, M3 color schemes, and dynamic tokens |
| `cli` | `qtmaterial3-cli` package (`doctor`, `run`, `create`, `icon_explorer`, `designer`) |
| `designer` | `qtmaterial3-designer` package (TaskMenu extension, dialogs, custom property editors) |
| `workspace` | Root workspace configuration, `Makefile`, root `pyproject.toml`, monorepo dependencies |

*(Note: Scope can be omitted only for broad changes that affect the entire repository, e.g. `chore: upgrade ruff to 0.16.5`).*

## Critical Rules

- **NEVER add `Co-Authored-By` or any AI attribution trailers**: The Git log must remain clean, professional, and standard.
- **One logical concern per commit**: Keep commits atomic. Never mix refactors, feature additions, and documentation in a single commit.
- **Use imperative mood in the subject line**: "add" not "added", "fix" not "fixed", "refactor" not "refactored".
- **Keep subject line ≤ 72 characters**: Be concise and self-explanatory.
- **Explain "Why" in the commit body when necessary**: If a change has non-obvious context or tradeoffs, leave a blank line after the subject line and add an explanatory paragraph.

## Examples

```text
feat(designer): add visual icon picker dialog and autocomplete
fix(buttons): resolve icon color override precedence in paint event
refactor(designer): modularize package architecture into core, configs, and editors
test(designer): split monolithic extension tests into granular suites
build(workspace): standardize pyproject.toml build system to setuptools
docs(designer): add comprehensive package README and usage examples
chore(workspace): remove mypy in favor of pyright
```

## Anti-patterns

```text
# BAD — vague message
update stuff

# BAD — AI attribution trailer
feat(designer): add color picker

Co-Authored-By: Claude <claude@anthropic.com>

# BAD — multiple concerns mixed together
feat(designer): add icon picker and fix button color bug and update readme

# BAD — past tense
fix(buttons): fixed the icon color not updating
```
