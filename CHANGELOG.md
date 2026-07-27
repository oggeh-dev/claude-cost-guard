# Changelog

## Unreleased

### Fixed

- **Rates are per model, not per tier.** `model_rates()` matched `opus` as a substring of the
  model id, so every `claude-opus-5` session was priced at Opus 4.1 rates — $15/$75 instead of
  $5/$25. On a real 239-turn session that reported **$276.16 instead of $74.91, a 3.69x
  over-estimate**, which means a $10 session cap halted at roughly $2.71 of actual spend. The
  tier abstraction was sound while every Opus release shared a price; Opus 4.1 and Opus 5 sit
  3x apart in the same tier.
- **Effective-date ranges.** Pricing changes on dates — Claude Sonnet 5 moves from $2/$10 to
  $3/$15 on 2026-09-01 — so a session is now priced by *its own* date. Without this, every
  historical figure silently changes overnight.
- **`speed`, `inference_geo` and web search are no longer ignored.** All three are in the
  transcript's `usage` and were dropped: fast mode (Opus 5/4.8 at $10/$50) was under-counted by
  half, `inference_geo: "us"` missed its 1.1x multiplier, and web search ($10 per 1,000
  requests) was not counted at all.

### Added

- **`cost-guard refresh-pricing`** — re-derives rates from the published pricing page. The only
  command that touches the network, never called from a hook. Without it `last_verified` is a
  comment nobody acts on, which is how the table drifted three months out of date. It reads the
  docs' source markdown (`<path>.md`); the HTML path is a 1 MB SPA shell whose table is built
  client-side. It **fails safe**: an unfetchable page or an unparseable layout leaves the table
  untouched and exits non-zero rather than writing zeros. It refuses to flatten models with
  dated periods, because collapsing two periods into one reprices history.
- **Staleness is visible.** `status --json` reports `pricing.last_verified`, `age_days` and
  `stale` against `max_age_days`. Halts keep working when stale — the fallback deliberately
  over-estimates, which fails safe for a guard — but the condition is no longer invisible.
- **`tests/test_pricing.py`** — 25 tests over rate resolution, effective dates, fast mode,
  derived cache multipliers, the modifiers, staleness and table integrity. This is money math
  driving a halt and it shipped untested; the 3.69x defect is what hid in that gap.

### Changed

- Cache rates are **derived** from the documented multipliers (5m write 1.25x, 1h write 2x,
  read 0.1x) rather than stored per model, so only input and output need maintaining.
- The tier table remains as a **fallback** for a model id newer than the table, and
  `model_rates()` now returns `priced_by` so a caller can tell a real rate from a guess. The
  fallback stays deliberately expensive: for a halt guard, over-estimating an unknown model
  fails safe, while under-estimating lets a runaway loop through.

All notable changes to `cost-guard` are documented here. This project uses [semantic versioning](https://semver.org).

## [0.1.4] — 2026-04-26

### Fixed

- **Slot metric no longer drifts downward and no longer spikes at slot resets.** The previous per-session formula (`sess_cost / slot_share` extrapolation) assumed the current session was the sole consumer of the 5-hour slot; when other sessions burned percentage points without this session burning $ proportionally, the implied cap dropped and the displayed `🎰 slot: $X` visibly decreased. Replaced with `global_5h_cost_usd / (slot_pct/100)` — the all-sessions trailing-5h cost divided by Claude Code's account-wide slot percentage, anchored to the current slot period via `rate_limits.five_hour.resets_at` so spending from a previous slot period doesn't pollute the new period's projection. Right after a slot reset there is a brief calibrating window (gates: `slot_pct ≥ 0.5%` AND ≥ $0.05 of cost-guard-tracked spending in the current period) — typically seconds to a few minutes — after which the dynamic estimate kicks in and `X = Y × Z/100` always holds. The cap honestly reflects the current period's $-per-pp ratio (depends on Opus / Sonnet / Haiku mix, cache hit rates, output ratios — generally not the same as the previous period's).
- **Duplicate-append bug in `ingest_transcript` (root cause of inflated cost reports).** Cross-checking against ground-truth JSONL math on a 1h51m heavy-subagent session showed cost-guard reporting $208.82 vs ground truth $120.10 — a $89 phantom-cost inflation. Ledger entries were exact duplicates: same ts, same session_id, same origin, same cost. Root cause: read-modify-write race in `ingest_transcript`. Multiple hooks fire close in time (PreToolUse, PostToolBatch, SubagentStart). Each loads the same `last_ingested_ts`, finds the same new transcript entries, and each appends them. Sessions with heavy subagent fan-out hit the worst dup rates (50% / 8% / 0% across three sessions ranked by subagent count). Three-layer defense: (1) `ingest_transcript` now wraps its read-modify-write in an exclusive `fcntl.flock`, serializing concurrent hooks; falls through gracefully on platforms without `fcntl` (Windows). (2) `_dedupe_rows` helper applied on every read in `global_5h_cost_usd`, `session_cost_usd`, `session_rate_per_min_usd`, `current_turn_cost_usd` — fixes displayed totals immediately on dirty existing ledgers, before the file is ever rewritten. (3) `ledger_compact` now also deduplicates on every `SessionStart`, so the ledger file gets cleaned up over time and doesn't grow unbounded with phantom rows.

### Added

- README — new "Known limitations" section consolidating three caveats users should be aware of: (a) **non-Claude-Code activity** — cost-guard only sees costs in JSONL transcripts under `~/.claude/projects/`, so claude.ai web/desktop activity counts against the slot but not the ledger, making the cap estimate a lower bound for users who split work across surfaces; (b) **idle-session payload staleness** — Claude Code populates `rate_limits` and `context_window` in the status-line stdin payload from response headers of the last API call in *that specific session*, so an idle session's indicator displays a slot percentage frozen at its last activity even though `$X` and `≈$Y` (which come from shared on-disk files) update normally; (c) **slot-reset calibrating window** — brief moment of `🎰 slot: N% (calibrating)` right after a 5-hour reset until the new period accumulates $0.05 / 0.5% slot of data.

## [0.1.3] — 2026-04-26

### Fixed

- **`allowed-tools` patterns shipped in 0.1.2 didn't match the actual expanded bash command, so slash commands continued to hard-fail.** The patterns used `*"cost-guard" <subcommand>*`, expecting both an opening and closing `"` adjacent to `cost-guard`. The real expanded command places the opening `"` at the start of the binary path (`"/Users/.../bin/cost-guard"`), so only the closing `"` is adjacent. Fixed by changing every skill's pattern to `*/cost-guard" <subcommand>*` — slash before `cost-guard` (path separator), closing quote after.

## [0.1.2] — 2026-04-26

### Fixed

- **Slash commands no longer hard-fail with `Shell command permission check failed`.** Every `/cost-guard:*` skill now declares a narrowly-scoped `allowed-tools` Bash pattern in its `SKILL.md` frontmatter, matching the pattern Anthropic's own plugin-dev examples use for slash commands that contain `!`…`` shell expansion. Without this, Claude Code's permission engine refused every invocation outright (no dialog, just an error). The patterns are scoped per-skill to the specific cost-guard subcommand they invoke.
- **`/cost-guard:install-indicator` actually installs end-to-end.** Previously it printed manual-edit instructions on stderr and required the user to paste the JSON snippet into `~/.claude/settings.json` by hand, because the plugin sandbox blocks plugin processes from writing to that file directly. The skill is now model-invokable and declares `Edit(~/.claude/settings.json)` in `allowed-tools`; the binary emits a machine-readable `cost-guard:apply-statusline:<JSON>` directive on stdout when the direct write is sandbox-denied; the skill instructs Claude to parse that line and apply the change via the Edit tool. Manual-paste fallback on stderr is still emitted so any direct-shell user gets the same instructions as before.
- **Burn-rate halt no longer re-evaluates on every hook fire.** The rate halt branch in `evaluate_and_maybe_halt` was running on every `PreToolUse` / `PostToolBatch` / `PreCompact` event — several times per minute on a busy turn — producing redundant halts and noisy `halt-log.jsonl` entries. The branch now skips evaluation if less than 60 seconds have passed since the last rate check (tracked in session state as `last_rate_check_ts`). The 5-minute trailing-rate window already smoothed the *value*; this change limits how often the *halt decision* is re-applied. The indicator's displayed rate is unaffected and continues to update at every status-line refresh.

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
