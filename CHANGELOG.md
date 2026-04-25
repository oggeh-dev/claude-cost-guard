# Changelog

All notable changes to `cost-guard` are documented here. This project uses [semantic versioning](https://semver.org).

## [0.1.1] — 2026-04-25

### Fixed

- **Indicator's step cell now stays accurate under `enabled: false`.** The step counter (`👣 step: $X (cap $Y)`) was silently sticking at `$0.00` whenever cost-guard was disabled. Root cause: `turn_start_ts` — the field the indicator reads to know where the current step began — was only ever written by the `SessionStart` / `UserPromptSubmit` hook handlers, which short-circuit on `enabled: false`. With no `turn_start_ts` in session state, the `or time.time()` fallback in `_render_cost_guard_row` filtered the ledger for entries with `ts >= now`, which is always empty. Fix: `cmd_halt_check` now writes `turn_start_ts` unconditionally on `SessionStart` / `UserPromptSubmit`, before the `enabled` gate — the same pre-gate pattern `ingest_transcript` already uses to keep session/rate metrics live in disabled mode. The post-gate handlers still write it too; doing so twice is idempotent. Slot/session/rate were unaffected (slot is indicator-self-managed; session/rate read the pre-gate-populated ledger directly).

## [0.1.0] — 2026-04-25

Initial release. Local development only; not yet published to the official marketplace.

### Design

Enforcement runs entirely from hooks reading the JSONL transcript Claude Code writes for every session. The plugin has no UI surface and does not depend on any other plugin or configuration. All thresholds are in USD.

### Enforcement

- **Per-session USD cap** (`max_usd_per_session`, default $10). `UserPromptSubmit` blocks new prompts and `PostToolBatch` halts mid-step when session spend crosses it.
- **Per-step USD cap** (`max_usd_per_step`, default $2). `PostToolBatch` halts the agentic loop between model iterations if one step has spent more than this.
- **Burn-rate cap** (`rate_per_min_usd`, default $0.50/min). Trailing 5-minute session-filtered rate. Enforced at every `UserPromptSubmit`, `PreToolUse`, and `PostToolBatch`.
- **Subagent fan-out cap** (`max_subagent_spawns_per_step`, default 8). `PreToolUse` with `matcher: "Agent|Task"` denies further spawns in the same step.
- **Compaction gate.** `PreCompact` halts if any cap has already been crossed (compaction is an expensive hidden model call).

### Added

- Plugin manifest with `userConfig` for 8 fields: `enabled`, `max_usd_per_session`, `max_usd_per_step`, `rate_per_min_usd`, `max_subagent_spawns_per_step`, `warn_at_usd`, `seed_from_history`, `log_decisions`.
- Hook registrations: `SessionStart`, `UserPromptSubmit`, `PreToolUse` (matcher `Agent|Task`), `PostToolBatch`, `PreCompact`, `SubagentStart`.
- Eleven plugin skills: `/cost-guard:status`, `:diag`, `:set-session-limit`, `:set-step-limit`, `:set-rate`, `:set-subagent-cap`, `:set-warn`, `:pause`, `:resume`, `:install-indicator`, `:uninstall-indicator`.
- **Optional bottom-row indicator** via `/cost-guard:install-indicator`. Compose-mode default: wraps any existing bottom-row command and appends cost-guard's rows below; replace-mode backs up the prior command for byte-exact restore on uninstall. Pure convenience — halts run identically without it. Default `refreshInterval` is 2 seconds.
- **Three-line indicator** with column-aligned layout (line 3 suppressed when no extra info is available):
  - Line 1: `Cost Guard — token-cost watchdog` header (OGGEH brand pink `#ec638d` + bold name, dim tagline). Header changes to `Cost Guard (paused)` in yellow when halts are paused, `Cost Guard (HALTED) — <reason>` in red whenever a halt has just fired (clears on next non-bypass user prompt), or `Cost Guard (off)` in dim when globally disabled.
  - Line 2: `💵 session: $X (cap $Y)` · `🔥 rate: $X/min (limit $Y)` · `👣 step: $X (cap $Y)` — green/amber/red by threshold.
  - Line 3: `🧠 ctx: N%` and, on Pro/Max plans, `🎰 slot: $X of ≈$Y plan (N%)`.
  - Cells on line 3 align under cells on line 2 — column widths computed from `max(visual_width(top), visual_width(bottom))` per column, accounting for emoji being 2-cell-wide.
  - When the slot USD estimate isn't yet computable (session hasn't moved the slot ≥ 0.1% yet), the cell collapses to `🎰 slot: N% (calibrating)` to keep the layout tight.
- `CLAUDE_PLUGIN_DATA` fallback now points at `.../cost-guard-inline/` (matching Claude Code's own path for `--plugin-dir`-loaded plugins) so CLI-from-shell invocations read the same data directory the hook subprocesses write to, even when the env var is unset.
- `/cost-guard:diag` skill dumps file sizes, env vars, recent halt-log entries, effective config, and the current bottom-row command — for debugging.
- **Skills pass `CLAUDE_PLUGIN_DATA` through explicitly.** Claude Code exports the env var to hook subprocesses but not to shell-injected skill subprocesses; without the explicit pass-through, skills fell back to a different data dir than the hooks wrote to. All 11 skills now set both `CLAUDE_PLUGIN_DATA` and `CLAUDE_PLUGIN_ROOT` at the command line.
- **UserPromptSubmit hook only halts on session-over-cap.** Rate and per-step caps apply during a step (PostToolBatch / PreToolUse), not to starting one — halting a new prompt on a trailing rate locks the user out of cost-guard's own escape-hatch slash commands.
- **Escape hatch:** prompts starting with `/cost-guard:` or `/exit` / `/quit` bypass the UserPromptSubmit halt unconditionally, so the user can always adjust caps, pause, or exit.
- Single-binary CLI at `bin/cost-guard` (Python 3 stdlib only, no runtime dependencies).
- Persistent rolling 5-hour cost ledger in `${CLAUDE_PLUGIN_DATA}/cost-ledger.jsonl`, session-filtered for all halt decisions.
- Optional history seeding on first install via `seed_from_history` (default on) so burn-rate calculations are accurate on prompt #1 after install.
- Halt audit log in `${CLAUDE_PLUGIN_DATA}/halt-log.jsonl`.
- Pricing table at `pricing.json` for opus / sonnet / haiku tiers with model-tier matching rules.
