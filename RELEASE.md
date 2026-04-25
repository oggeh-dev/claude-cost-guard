# Release process

How to ship a new release of `cost-guard`. This is a standalone Claude Code plugin repository — the release flow below is fully self-contained.

## Versioning policy

Standard [semantic versioning](https://semver.org/) — `MAJOR.MINOR.PATCH`.

| Bump | When | Examples |
|---|---|---|
| **PATCH** (`0.1.0 → 0.1.1`) | Bug fix, doc update, pricing-table refresh — anything that doesn't change behavior users rely on. | Halt-banner typo. JSONL parser bug. Anthropic pricing changed. README clarification. |
| **MINOR** (`0.1.0 → 0.2.0`) | Backwards-compatible feature: anything that adds capability without changing or removing existing behavior. | New `/cost-guard:*` skill. New `userConfig` field with a default. New halt event. New indicator metric. |
| **MAJOR** (`0.1.0 → 1.0.0`) | Breaking change: anything that requires users to update their config, mental model, or expectations. | Renaming a `userConfig` key. Removing a skill. Changing the meaning of an existing field. |

**Pre-1.0 exception:** while the leading version is `0.x.y`, breaking changes are allowed to bump `MINOR`. Once we ship `1.0.0`, strict semver applies.

---

## Files to update on every release

### 1. `.claude-plugin/plugin.json`

Bump `"version"`. This is the field Claude Code uses to detect "has the user got the latest?". **Skipping this bump is the most common release mistake** — users running `/plugin update cost-guard@oggeh` will see "already at the latest version" and miss your release.

### 2. `CHANGELOG.md`

Add a new section at the top, above the previous release entry:

```markdown
## [0.2.0] — YYYY-MM-DD

### Added
- …

### Changed
- …

### Fixed
- …
```

Use [Keep a Changelog](https://keepachangelog.com/) headings (`Added` / `Changed` / `Fixed` / `Deprecated` / `Removed` / `Security`).

That's it — these are the only two files this repo's release flow touches.

---

## Step-by-step release

```bash
# 1. (Optional) Branch for the release commit. Working directly on main is fine for solo maintenance.
git checkout -b release/v0.2.0

# 2. Edit .claude-plugin/plugin.json + CHANGELOG.md.

# 3. Validate.
claude plugin validate .

# 4. Commit.
git add .claude-plugin/plugin.json CHANGELOG.md
git commit -m "release: cost-guard v0.2.0"

# 5. Merge to main and clean up the branch.
git checkout main
git merge --ff-only release/v0.2.0
git branch -d release/v0.2.0

# 6. Dry-run the tag. This validates plugin.json and prints the tag name without creating it.
claude plugin tag . --dry-run

# 7. Create + push the tag in one step.
claude plugin tag . --push -m "cost-guard v0.2.0"

# 8. Push the release commit.
git push origin main
```

The tag format is `cost-guard--v0.2.0` — the `claude plugin tag` command derives it from `plugin.json`'s `name` and `version` fields.

---

## How users get the update

After your push:

```
/plugin update cost-guard@oggeh
```

If the user has enabled auto-update for the `oggeh` marketplace (third-party marketplaces have it OFF by default; the user must opt in via `/plugin` → Marketplaces tab), Claude Code refreshes on next start and prompts them to run `/reload-plugins`.

---

## Special-case releases

### Pricing-table refresh

Edit `pricing.json` (update rates and bump `_metadata.last_verified` to today). Bump patch in `plugin.json`.

CHANGELOG entry under `### Changed`:
```markdown
- Pricing table refreshed against Anthropic's published rates as of YYYY-MM-DD.
```

### Hot fix on a published release

1. Branch from the broken release tag: `git checkout -b hotfix/v0.2.1 cost-guard--v0.2.0`.
2. Fix the bug. CHANGELOG under `### Fixed`.
3. Bump patch in `plugin.json`.
4. Run the standard release procedure.

---

## Pre-flight checklist

Before tagging:

- [ ] `claude plugin validate .` passes.
- [ ] `plugin.json.version` matches the new CHANGELOG section heading.
- [ ] CHANGELOG has a dated section for the new version with all user-visible changes documented.
- [ ] If `pricing.json` changed, `_metadata.last_verified` is today.
- [ ] All hook commands still resolve (`grep CLAUDE_PLUGIN_ROOT hooks/hooks.json`).
- [ ] `git status` is clean.
- [ ] `claude plugin tag . --dry-run` prints the expected tag name.

After pushing:

- [ ] The commit appears at `oggeh-dev/claude-cost-guard`.
- [ ] The tag `cost-guard--v<NEW>` appears in the GitHub releases / tags view.
- [ ] In a fresh Claude Code session: `/plugin update cost-guard@oggeh` pulls the new version.
- [ ] `/cost-guard:status` shows `enabled: true` and the new behavior is in effect.

---

## Reference

- [Claude Code plugin docs](https://code.claude.com/docs/en/plugins)
- [Marketplace docs](https://code.claude.com/docs/en/plugin-marketplaces)
- [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
- [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
