---
name: release-notes
description: "Trigger: release, release notes, changelog, tag, version. Run the qtframelesskit release process: draft release notes, verify version consistency, create annotated tags, update changelog, and coordinate GitHub Releases."
license: MIT
metadata:
  author: BugCodeX
  version: "1.0"
---

# Skill: release-notes

## Purpose

Enforce a standardized, structured release process for **qtframelesskit**, including drafting user-facing release notes from conventional commits, verifying version consistency across configuration and source files, maintaining `CHANGELOG.md`, and coordinating Git tags and GitHub Releases with strict confirmation gates.

## When to Use

Any time a release, release notes, changelog entry, version tag, or GitHub Release is drafted, prepared, or published for `qtframelesskit`.

---

## Critical Rules

- **Read commits since previous tag**: Always inspect the exact range: `git log --oneline <prev>...<next>`.
- **Group by conventional commit type**: Categorize commits into user-facing sections; never dump a raw or unformatted commit list.
- **Filter internal commits**: Exclude internal `ci` and routine `chore` commits unless they directly affect library consumers or packaging.
- **Omit empty sections entirely**: Never write "No fixes in this release" or create empty headers.
- **Verify version consistency**: Ensure `pyproject.toml` (`version = "X.Y.Z"`) and `src/qtframelesskit/__init__.py` (`__version__ = "X.Y.Z"`) match the target release tag exactly.
- **Mandatory Verification section**: Every release note must include verification instructions for installing with optional Qt bindings (`[pyside6]` or `[pyqt6]`) and checking `qtframelesskit.__version__`.
- **STRICT GATE**: NEVER create tags (`git tag`) or publish GitHub Releases (`gh release create`) without explicit user confirmation.

---

## Decision Gates

| Situation | Action |
| --- | --- |
| User asks for draft release notes or changelog preview | Generate the release notes document; do NOT create a tag or GitHub Release. |
| User asks to release / publish a version | Verify version consistency, draft release notes, and **pause for explicit user approval** before running `git tag` or `gh release create`. |
| Documentation or README is outdated for the release | Update documentation in a separate commit prior to creating the release tag. |
| Version mismatch between `pyproject.toml` and `__version__` | Halt release process immediately and reconcile versions before proceeding. |

---

## Execution Steps

1. **Inspect Commit History**:
   Read all commits since the previous tag:

   ```bash
   git log --oneline <prev>...<next>
   ```

2. **Group Commits by Type**:
   - `What's New`: `feat` commits introducing new capabilities, window effects, or public APIs.
   - `Changes`: `refactor`, `style`, `perf`, or `build` commits that impact library consumers.
   - `Fixes`: `fix` commits resolving bugs, crashes, or rendering issues.
   - `Documentation`: `docs` commits if significant to users (e.g., major documentation overhauls, new tutorials).
   - Exclude routine internal `chore` and `ci` commits.

3. **Verify Version Consistency**:
   Confirm that the target version `X.Y.Z` is identical in:
   - `pyproject.toml` (`version = "X.Y.Z"`)
   - `src/qtframelesskit/__init__.py` (`__version__ = "X.Y.Z"`)

4. **Request Explicit User Confirmation (MANDATORY GATE)**:
   Present the draft release notes and ask for confirmation before creating any tag or GitHub Release.

5. **Create and Push Annotated Tag**:
   Once confirmed, create an annotated local tag and push:

   ```bash
   git tag -a vX.Y.Z -m "qtframelesskit vX.Y.Z"
   git push origin <branch>
   git push origin vX.Y.Z
   ```

6. **Update CHANGELOG.md**:
   Prepend the new release section to `CHANGELOG.md` using the exact release notes content.

7. **Create GitHub Release**:
   Publish the release using the GitHub CLI:

   ```bash
   gh release create vX.Y.Z --title "qtframelesskit vX.Y.Z" --notes-file <file>
   ```

---

## Release Notes Output Format

```markdown
# qtframelesskit vX.Y.Z

## What's New
<!-- feat commits: new features, APIs, and capabilities -->
- Short description of the feature

## Changes
<!-- refactor, perf, style, build commits with user impact -->
- Short description of the change

## Fixes
<!-- fix commits: bug and crash fixes -->
- Short description of the fix

## Documentation
<!-- docs commits: significant documentation improvements (omit if none) -->
- Short description of documentation update

## Verification
<!-- Mandatory section: commands to validate installation and version -->
```bash
# Install with preferred binding
pip install qtframelesskit[pyside6]==X.Y.Z  # or qtframelesskit[pyqt6]==X.Y.Z
python -c "import qtframelesskit; print(qtframelesskit.__version__)"
```

---

## Section Rules

| Section | Include | Omit |
| --- | --- | --- |
| **What's New** | `feat` commits with user-facing features or new APIs | Internal features with no public exposure |
| **Changes** | `refactor`, `perf`, `style`, `build` with consumer impact | Pure internal refactoring or maintenance |
| **Fixes** | `fix` commits resolving user-facing bugs or edge cases | Typo fixes in internal comments |
| **Documentation** | Significant documentation additions or guides | Minor README typo corrections |
| **Verification** | Always present with binding options and import check | Never omit — this section is mandatory |

---

## Example

```markdown
# qtframelesskit v0.1.0

## What's New
- Pure Python frameless window implementation with native Windows snap layouts
- Acrylic and Mica backdrop material support via DWM APIs
- TitleBar widget with native Windows caption button integration

## Verification
```bash
# Install with preferred binding
pip install qtframelesskit[pyside6]==0.1.0  # or qtframelesskit[pyqt6]==0.1.0
python -c "import qtframelesskit; print(qtframelesskit.__version__)"
```

---

## Anti-patterns

```markdown
# BAD — Raw commit dump
- 7b1c3e4 fix: resolve snap layout flicker
- 2a4d9f1 chore: update ruff config

# BAD — Empty section filler
## Fixes
- None in this release.

# BAD — Missing Verification section
## What's New
- Added mica effect
(end of notes)

# BAD — Vague descriptions
- Bug fixes and performance improvements
```
