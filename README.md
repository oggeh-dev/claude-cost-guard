# cost-guard

**Real-time USD cost enforcement for Claude Code.** Halts runaway agentic loops mid-step before they burn through your budget.

`cost-guard` is a Claude Code plugin. Once installed, it runs automatically on every session and every prompt:

- **Mid-step halt** (via the `PostToolBatch` hook) stops the agentic loop between model iterations if the current step's cost, the session's total cost, or the burn rate crosses its configured limit. This keeps one greedy step from cascading into a $30+ spend in minutes.
- **Subagent fan-out cap** (via `PreToolUse`) denies additional `Agent`/`Task` spawns inside a single step once the per-step spawn count is reached.
- **Prompt gate** (via `UserPromptSubmit`) blocks the next user prompt if the session has already exceeded its cap, rate, or step limit.
- **Compaction gate** (via `PreCompact`) blocks context compaction when the budget is already crossed (compaction is an expensive hidden model call).

All enforcement runs from hooks reading the JSONL transcript Claude Code writes for every session. All thresholds are in USD. No network calls. Python 3 standard library only.

A **bottom-row indicator** is available as an opt-in extra — `/cost-guard:install-indicator` — that shows live cost metrics at the bottom of the Claude Code UI. It is purely cosmetic; halts run identically whether the indicator is installed or not. If you already have a bottom-row command configured (from `/statusline` or another plugin), the installer detects it and asks whether to *compose* (cost-guard runs your existing command and appends its own row below, both visible) or *replace* (cost-guard takes over; your previous command is backed up and restored by `uninstall-indicator`).

The indicator renders three lines when enough data is available:

```
Cost Guard — token-cost watchdog
💵 session: $1.23 (cap $10.00)    🔥 rate: $0.24/min (limit $0.50)    👣 step: $0.45 (cap $2.00)
🧠 ctx: 42%                       🎰 slot: $5.25 of ≈$15.00 plan (35%)
```

Header changes when state changes:

- **Active** — pink `Cost Guard — token-cost watchdog`
- **Paused** — yellow `Cost Guard (paused) — halts disabled for this session`
- **Halted** — red `Cost Guard (HALTED) — <human-readable reason>` (e.g. `burn rate over limit`, `session cap reached`, `step exceeded cap`, `subagent fan-out cap reached`). The badge clears on the next non-bypass user prompt — once you submit normal work, cost-guard takes that as acknowledgment that the cause was resolved.
- **Disabled globally** — dim `Cost Guard (off) — runaway protection disabled`

Columns on line 2 and line 3 align: the second column on line 3 (slot) starts at the same screen position as the second column on line 2 (rate). Cell colors follow the threshold logic — green under the warn level, amber between warn and cap, red at/over.

| Field | Meaning |
|---|---|
| `💵 session: $X (cap $Y)` | Current session USD spend vs the per-session cap. |
| `🔥 rate: $X/min (limit $Y)` | Trailing 5-minute USD burn rate vs the per-minute limit. |
| `👣 step: $X (cap $Y)` | USD spent in the current step vs the per-step hard cap. Resets on every new `UserPromptSubmit`. |
| `🧠 ctx: N%` | Percent of the Claude Code context window currently in use (from Claude Code's own data, always available). |
| `🎰 slot: $X of ≈$Y plan (N%)` | **For Claude.ai Pro/Max subscribers.** The estimated USD value your 5-hour rate-limit slot represents, and how many of those dollars have already been consumed across *all* sessions in the current window. Derived from this session's cost-to-slot ratio (`session_cost ÷ session_slot_share × 100`). Lets you map the USD caps onto your subscription's slot in actual-dollar terms: if `plan ≈ $15` and you've used `$5.25` (35%), you have about $9.75 of slot left before Anthropic throttles. Shown only once the session has a stable signal (≥ $0.05 spent and ≥ 0.1% slot movement). Before that, the cell collapses to `🎰 slot: N% (calibrating)`. |

### Every threshold is in USD

- **`max_usd_per_session`** (default `$10`) — hard cap on **total** spend across every step in this Claude Code session. Once cumulative session spend crosses this, `UserPromptSubmit` blocks new prompts and `PostToolBatch` halts any in-progress step.
- **`max_usd_per_step`** (default `$2`) — hard cap on what **one single step** can spend. A "step" is one prompt → Claude responds → tool batch → Claude responds → tool batch → ... until Claude stops. `PostToolBatch` halts the loop between tool batches as soon as the step's cost crosses this. Primary defense against a single greedy step.
- **`rate_per_min_usd`** (default `$0.50`) — trailing 5-minute session burn-rate cap.
- **`max_subagent_spawns_per_step`** (default `8`) — count-based cap on subagent fan-out per step.

**Why two caps?** They defend against different failure modes:

- A *long* session that slowly accumulates cost across many normal steps → `max_usd_per_session` catches it.
- A *greedy single step* (e.g., Claude fans out 20 subagents or runs 50 tool calls in one response cycle) → `max_usd_per_step` catches it mid-step, before the session cap has any reason to fire.

Example with defaults ($10 session, $2 per-step): you can have five normal $1.50 steps (total $7.50, neither cap tripped). But if one step starts burning through $3, cost-guard halts it at ~$2 before it can complete — without waiting for the session total to hit $10.

Session cost comes from the JSONL transcript (`transcript_path` is provided to every hook) multiplied by the shipped pricing table. Everything is derived from data the hook already has — nothing is read from any UI surface.

---

## Install

### From the OGGEH marketplace

```
/plugin marketplace add oggeh-dev/claude-plugins
/plugin install cost-guard@oggeh
```

The first command registers the marketplace catalog under the local name `oggeh`; the second installs the `cost-guard` plugin from it. Halts activate on the next `SessionStart`.

### Local development

This repository **is** the plugin (cost-guard's source lives at the root):

```bash
git clone git@github.com:oggeh-dev/claude-cost-guard.git
claude --plugin-dir claude-cost-guard
```

The `oggeh` marketplace at [`oggeh-dev/claude-plugins`](https://github.com/oggeh-dev/claude-plugins) catalogs this plugin via a `github` source, so the install commands above route Claude Code to fetch from this repo automatically — no special path needed.

---

## Commands

| Command | What it does |
|---|---|
| `/cost-guard:status` | Prints current session spend, rate, and configured caps. |
| `/cost-guard:diag` | Full plugin-state dump: file sizes, env vars, recent halts, effective config, current bottom-row command. Use this when something looks wrong. |
| `/cost-guard:set-session-limit <USD>` | Sets the per-session USD cap. |
| `/cost-guard:set-step-limit <USD>` | Sets the per-step USD cap. |
| `/cost-guard:set-rate <USD/min>` | Sets the per-minute burn-rate limit. |
| `/cost-guard:set-subagent-cap <N>` | Sets the max subagent spawns per step. |
| `/cost-guard:set-warn <USD>` | Sets the amber-warn threshold on session spend. |
| `/cost-guard:pause` | Globally disables halts (warning: runaway protection is off). |
| `/cost-guard:resume` | Re-enables halts. |
| `/cost-guard:install-indicator [compose\|replace]` | Install the bottom-row indicator. With no argument, if a bottom-row command is already configured, cost-guard shows the choice and exits without modifying anything. |
| `/cost-guard:uninstall-indicator` | Remove cost-guard's indicator and restore whatever was there before (compose / replace backups are byte-exact restores). |

The shipped binary is also on PATH while the plugin is enabled, so you can run it directly from any shell:

```bash
cost-guard status
cost-guard set-session-limit 30
cost-guard status --json
```

---

## Configuration

All knobs are declared in `plugin.json` as `userConfig` fields. Claude Code prompts for each value when the plugin is enabled. You can override any field at runtime via `/cost-guard:set-*` commands (stored in `${CLAUDE_PLUGIN_DATA}/overrides.json`).

| Field | Default | Description |
|---|---|---|
| `enabled` | true | Master switch. When false, no halts fire. |
| `max_usd_per_session` | 10.00 | Hard cap on total session spend. `UserPromptSubmit` and `PostToolBatch` halt when the session ledger crosses this. |
| `max_usd_per_step` | 2.00 | Hard cap per single Claude step. `PostToolBatch` halts when one step crosses this. Primary defense against one greedy step. |
| `rate_per_min_usd` | 0.50 | Trailing 5-minute burn-rate cap. Session-filtered. |
| `max_subagent_spawns_per_step` | 8 | `PreToolUse` denies further `Agent`/`Task` tool calls within a step once this count is reached. |
| `warn_at_usd` | 7.00 | Amber warning on `UserPromptSubmit` when session spend crosses this (below cap). |
| `seed_from_history` | true | On first install, scan recent `~/.claude/projects` transcripts to populate the rolling ledger. Gives accurate trailing burn-rate on prompt #1 after install. |
| `log_decisions` | true | Write every halt/warn to `${CLAUDE_PLUGIN_DATA}/halt-log.jsonl`. |

All cost data comes from the JSONL transcripts Claude Code writes for every session. The pricing table ships in `pricing.json` and is verified against Anthropic's public rates. No network calls.

---

## How the halt works

Claude Code exposes hooks that fire at specific lifecycle events. Two of them can stop an agentic loop mid-run:

1. **`PostToolBatch`** — fires after every batch of tool calls, before the next model invocation. Exit code 2 here stops the loop. This is the primary defense against a $4/min runaway: once the step cost, session cost, or session burn rate crosses the limit, the plugin stops the loop before the next model call can compound the spend.
2. **`PreToolUse`** with matcher `Agent|Task` — fires before each tool call. Exit code 2 denies the specific call. Used to cap subagent fan-out within a single step.

Other supporting hooks:

- **`UserPromptSubmit`** gates the next prompt when the session cap, rate limit, or step cap is already blown.
- **`PreCompact`** blocks compaction when the budget is tight (compaction is an expensive hidden model call).
- **`SessionStart`** seeds the ledger on first install.

Every hook invocation is the same command: `${CLAUDE_PLUGIN_ROOT}/bin/cost-guard halt-check`. The binary dispatches internally based on the `hook_event_name` field.

### Exit codes

| Code | Meaning |
|---|---|
| `0` | Allowed. Either the budget is fine, cost-guard is disabled, or the session is paused. |
| `2` | Halted. `stderr` explains the breach and lists the exact commands to raise the limit, pause, or end the session. |
| Other | Never produced. Plugin bugs are caught at the top level and exit 0 so Claude Code is never blocked by a defect in this code. The failure is logged to `halt-log.jsonl`. |

---

## State and data files

All persistent state lives in `${CLAUDE_PLUGIN_DATA}` which Claude Code resolves to `~/.claude/plugins/data/<plugin-id>/` for marketplace installs or a local equivalent for `--plugin-dir` development:

| File | Purpose |
|---|---|
| `cost-ledger.jsonl` | Append-only rolling 5-hour cost log. Compacted on every `SessionStart`. |
| `overrides.json` | Runtime overrides set by `/cost-guard:set-*` commands. |
| `sessions/<session-id>.json` | Per-session state: step start, subagent spawn counter, paused flag, last-ingested transcript timestamp. |
| `halt-log.jsonl` | Audit log of every halt, warn, and error decision. |
| `.seeded` | Marker file indicating `seed_from_history` has run once. Delete to re-seed. |
| `indicator.json` | Present only if you installed the bottom-row indicator. Records which mode (`solo`/`compose`/`replace`), the wrapped command (compose mode), and the exact `statusLine` entry backed up at install time for byte-for-byte restore on uninstall. |

---

## Reinstalling, uninstalling, resetting

- **Reinstall / update:** re-run `/plugin install cost-guard@<owner>` or swap the `--plugin-dir`. `${CLAUDE_PLUGIN_DATA}` survives.
- **Re-seed from history:** delete `${CLAUDE_PLUGIN_DATA}/.seeded`. The next `SessionStart` will rebuild the ledger from `~/.claude/projects`.
- **Uninstall:** `/plugin uninstall cost-guard@<owner>`. Pass `--keep-data` to preserve the ledger in case you re-install later.
- **Reset everything:** delete `${CLAUDE_PLUGIN_DATA}`.

---

## Troubleshooting

**Halts fire too often.** Raise `max_usd_per_session`, `max_usd_per_step`, or `rate_per_min_usd`. All three are configurable at runtime via the `set-*` skills.

**Halts never fire.** Run `/cost-guard:status` and confirm `enabled: true`. Check `${CLAUDE_PLUGIN_DATA}/halt-log.jsonl` for recorded decisions; if it is empty, the hooks may not be registered — confirm via `claude --debug`.

**Halt fired but I need to ship.** Run `/cost-guard:pause` to disable until you explicitly `/cost-guard:resume`. Or raise whichever limit tripped (`set-session-limit`, `set-step-limit`, or `set-rate`).

---

## License

MIT — see [LICENSE](./LICENSE).
