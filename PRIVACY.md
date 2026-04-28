# Privacy Policy — `cost-guard`

**Effective date:** 2026-04-25
**Maintainer:** OGGEH, Inc

---

## TL;DR

`cost-guard` is a fully local Claude Code plugin. It makes **zero network requests**, sends **no data anywhere**, and contains **no analytics, telemetry, or crash reporting**. Everything it reads and writes stays on your machine, in directories Claude Code already controls. If you uninstall the plugin, all of its state goes with it.

---

## What `cost-guard` does

The plugin enforces real-time USD cost limits on your Claude Code sessions. To do that, it needs to know how many tokens each turn has used. It learns that by reading the **session transcript file Claude Code already writes for every session** (the file at `transcript_path`, which Claude Code passes to every hook). The plugin parses that file locally, multiplies usage by the prices in the bundled `pricing.json` table, and decides whether to halt.

It also writes a small amount of state to disk, all of it on your machine.

## Data the plugin reads

| What | Where it comes from | Why it's read |
|---|---|---|
| Session JSONL transcript | `transcript_path` (passed by Claude Code on every hook call; lives under `~/.claude/projects/`) | To compute per-turn USD cost from token counts |
| `rate_limits.five_hour.used_percentage` | Statusline-input JSON (only present if the optional indicator is installed and you're on a Claude.ai Pro/Max plan) | Informational display only |
| `context_window.used_percentage` | Statusline-input JSON (only when the optional indicator is installed) | Informational display only |
| `~/.claude/projects/*/*.jsonl` (recent files only, on first install) | Your local Claude Code transcripts | One-time seed of the rolling cost ledger so the burn-rate metric is accurate on prompt #1; this is the **only** time the plugin scans transcripts outside the active session, and only if `seed_from_history: true` (the default — you can disable it) |

The plugin **does not** read your prompts, code, files, environment variables, or any other data outside the lists above.

## Data the plugin writes

All written exclusively to your local filesystem, under directories Claude Code itself manages:

| File | Purpose |
|---|---|
| `${CLAUDE_PLUGIN_DATA}/cost-ledger.jsonl` | Append-only rolling 5-hour cost log: timestamp, session id, model name, USD cost, origin tag |
| `${CLAUDE_PLUGIN_DATA}/halt-log.jsonl` | Audit trail of halt and warn decisions: timestamp, decision, reason, relevant metrics |
| `${CLAUDE_PLUGIN_DATA}/sessions/<session-id>.json` | Per-session state: turn start timestamp, subagent-spawn counter, paused flag, slot-tracking metadata |
| `${CLAUDE_PLUGIN_DATA}/overrides.json` | Runtime configuration overrides (set by `/cost-guard:set-*` slash commands) |
| `${CLAUDE_PLUGIN_DATA}/.seeded` | Marker file indicating the one-time history seed has run |
| `${CLAUDE_PLUGIN_DATA}/indicator.json` | *(Only when the bottom-row indicator is installed.)* Records the wrap mode and any pre-existing statusLine command that was preserved at install time |
| `~/.claude/cost-guard-indicator-backup.json` | *(Only when the bottom-row indicator is installed.)* Backup of `indicator.json` outside `${CLAUDE_PLUGIN_DATA}` so it survives plugin-data wipes |
| `~/.claude/settings.json` | *(Only when you explicitly run `/cost-guard:install-indicator`.)* The plugin writes a single `statusLine` entry pointing at its own renderer; any pre-existing entry is preserved in `indicator.json` and restored on uninstall. **No other field of `settings.json` is touched.** |

`${CLAUDE_PLUGIN_DATA}` is a directory Claude Code allocates to the plugin under `~/.claude/plugins/data/`. The plugin never writes anywhere outside that directory and `~/.claude/settings.json` (the latter only for the indicator-install case described above).

## Network activity

**None.** The plugin contains no network code and makes no HTTP, DNS, or socket calls. You can verify this yourself: `grep -RE 'urllib|requests|http|socket|tcp|udp' bin/cost-guard` on any release of the plugin returns no matches. The Python source is plain stdlib + the standard library only — no external dependencies of any kind.

## Third parties

- The plugin uses Anthropic's published pricing rates for opus / sonnet / haiku tiers, embedded as a static JSON table in the plugin (`pricing.json`). The plugin does not communicate with Anthropic, OGGEH, or any other party at runtime.
- If you install `cost-guard` from the [`anthropics/claude-plugins-community`](https://github.com/anthropics/claude-plugins-community) marketplace, your *Claude Code installation* may make standard GitHub clone requests when fetching the plugin. That activity is governed by Claude Code's own privacy policy and GitHub's privacy policy — `cost-guard` itself isn't involved.

## Your control

- **Inspect everything the plugin has stored:** run `/cost-guard:diag` inside Claude Code, or examine `~/.claude/plugins/data/cost-guard-*/` directly.
- **Wipe all plugin data:** delete the `${CLAUDE_PLUGIN_DATA}` directory (and `~/.claude/cost-guard-indicator-backup.json` if you installed the indicator). The plugin reseeds defaults on next session start; no remote sync exists to repopulate anything.
- **Disable the history-seeding step:** set `seed_from_history: false` in `userConfig` (or via the runtime overrides file). The plugin will then skip the one-time scan of past transcripts.
- **Uninstall:** running `/plugin uninstall cost-guard@claude-community` removes the plugin entirely. By default Claude Code deletes `${CLAUDE_PLUGIN_DATA}` along with the uninstall; pass `--keep-data` if you want to preserve the ledger across reinstalls.

## Changes to this policy

Changes to this document are committed to the plugin repository's git history at <https://github.com/oggeh-dev/claude-cost-guard>. The "Effective date" at the top will be updated whenever the substance of the policy changes. Cosmetic edits (typos, formatting) don't move the effective date.

## Contact

For privacy-related questions about `cost-guard` specifically, open an issue at <https://github.com/oggeh-dev/claude-cost-guard/issues> or reach OGGEH at <https://oggeh.com>.
