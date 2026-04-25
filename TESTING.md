# Local testing guide

Walk through every halt path end-to-end to verify the plugin works.

## Prerequisites

```bash
claude --plugin-dir /path/to/claude-cost-guard
```

`--plugin-dir` points at the plugin repo root (this repo IS the plugin). Halts activate on `SessionStart`. Nothing else is required — hooks run regardless of whether the bottom-row indicator is installed.

## Watch the audit log

In a second terminal:

```bash
tail -f ~/.claude/plugins/data/cost-guard-inline/halt-log.jsonl
```

> Claude Code sets `CLAUDE_PLUGIN_DATA` to `.../cost-guard-inline/` when the plugin is loaded via `--plugin-dir`. Run `/cost-guard:diag` any time to see the exact path in use.

Every halt, warn, deny, and error goes here with timestamp, event, reason, and metrics.

## Get a full state snapshot anytime

```
/cost-guard:diag
```

Shows every file (with sizes), env vars, recent halts, effective config, and the current bottom-row command. Use this any time something looks wrong — first thing to run.

---

## Important note about prompts that trigger halts

Halts via `PostToolBatch` only fire when **Claude makes a tool call** (Bash, Read, Edit, Write, etc.). A request Claude can answer from conversation context alone will never trigger this hook, because there is no tool batch to process.

The test prompts below are written to force Claude into a tool call. If you substitute your own prompt, make sure it requires Claude to actually run a tool — the phrase "use the Bash tool to run X" is the most reliable.

---

## Test 1 — rate-limit halt (fastest to trigger)

**Verifies:** `PostToolBatch` + exit 2 stops the agentic loop when session burn rate crosses `rate_per_min_usd`.

**Steps:**

1. Set a very tight rate:
   ```
   /cost-guard:set-rate 0.01
   ```

2. Force a tool call so `PostToolBatch` actually fires:
   > "Use the Bash tool to run `ls /tmp | head -5` and show me the output."

3. After the first batch resolves, `PostToolBatch` runs cost-guard. Any real step burns > $0.01/min, so the halt fires:
   ```
   Trigger: session burn rate $X.XX/min >= limit $0.01/min
   ```

4. Restore:
   ```
   /cost-guard:set-rate 0.5
   ```

5. Check `halt-log.jsonl` — expect `"decision":"halt"`, `"reason":"rate-over-limit"`.

---

## Test 2 — per-step USD cap halt

**Verifies:** `PostToolBatch` halts when one Claude step spends more than `max_usd_per_step`.

**Steps:**

1. Tight per-step cap:
   ```
   /cost-guard:set-step-limit 0.05
   ```

2. Loosen the other caps so this one trips first:
   ```
   /cost-guard:set-rate 10
   /cost-guard:set-session-limit 1000
   ```

3. Force a tool call:
   > "Use the Bash tool to run `wc -l bin/cost-guard pricing.json hooks/hooks.json` and show the output."

4. `PostToolBatch` fires; step cost crosses $0.05:
   ```
   Trigger: step cost $X.XX >= per-step cap $0.05
   ```

5. Restore:
   ```
   /cost-guard:set-session-limit 10
   /cost-guard:set-step-limit 2
   /cost-guard:set-rate 0.5
   ```

6. Check `halt-log.jsonl` for `"reason":"step-over-cap"`.

---

## Test 3 — per-session USD cap halt

**Verifies:** `PostToolBatch` halts when session cumulative cost crosses `max_usd_per_session`.

**Steps (organic, slow):**

1. Tight session cap:
   ```
   /cost-guard:set-session-limit 0.50
   ```

2. Do real work until session spend crosses $0.50 — any prompt that makes Claude use tools. For example:
   > "Create chess game at /tmp/chess"

3. Once cumulative cost >= $0.50, the next `PostToolBatch` halts:
   ```
   Trigger: session spend $X.XX >= cap $0.50
   ```

4. Restore:
   ```
   /cost-guard:set-session-limit 10
   ```

5. Check `halt-log.jsonl` for `"reason":"session-over-cap"`.

---

## Test 4 — subagent fan-out cap

**Verifies:** `PreToolUse` with `matcher: "Agent|Task"` denies `Agent`/`Task` spawns beyond `max_subagent_spawns_per_step` within a single step.

**Steps:**

1. Lower the cap:
   ```
   /cost-guard:set-subagent-cap 3
   ```

2. Loosen the other limits so they don't trip first:
   ```
   /cost-guard:set-session-limit 1000
   /cost-guard:set-step-limit 1000
   /cost-guard:set-rate 100
   ```

3. Ask for explicit parallel subagent dispatch:

   > "I need you to research 5 independent topics in parallel. Use the Explore subagent for each one. Dispatch all 5 concurrently so they run at once. The topics are:
   >
   > 1. How many lines are in bin/cost-guard?
   > 2. What does pricing.json contain?
   > 3. List the skills in the skills/ directory.
   > 4. What hook events are registered in hooks/hooks.json?
   > 5. Which file is the largest in the repo?
   >
   > Spawn all 5 Explore agents in a single batch."

4. Calls 1–3 succeed. Call 4 hits `PreToolUse` exit 2:
   ```
   Trigger: subagent fan-out cap reached (3 spawns this step, limit 3)
   ```

5. Restore:
   ```
   /cost-guard:set-subagent-cap 8
   /cost-guard:set-session-limit 10
   /cost-guard:set-step-limit 2
   /cost-guard:set-rate 0.5
   ```

6. Check `halt-log.jsonl` for `"decision":"deny"`, `"reason":"subagent-cap"`.

---

## Test 5 — pause / resume

**Verifies:** `/cost-guard:pause` disables all halts globally; `/cost-guard:resume` re-enables them.

**Steps:**

1. Tight rate that would normally halt:
   ```
   /cost-guard:set-rate 0.01
   ```

2. Pause:
   ```
   /cost-guard:pause
   ```

3. Force a tool call:
   > "Use the Bash tool to run `date` and show the output."
   
   No halt fires. The indicator (if installed) shows `cost-guard (disabled)` in dim.

4. Resume:
   ```
   /cost-guard:resume
   ```

5. Run the same prompt again. Halt fires as in Test 1.

6. Restore:
   ```
   /cost-guard:set-rate 0.5
   ```

7. Check `halt-log.jsonl` — between pause and resume there should be no halt records.

---

## Test 6 — indicator install & uninstall (optional — only if you want the bottom-row display)

**Verifies:** `/cost-guard:install-indicator` correctly detects an existing bottom-row command, offers a choice, composes or replaces it, and `/cost-guard:uninstall-indicator` restores the original.

**Steps:**

1. Start with your existing `/statusline` configured (or no bottom-row command at all).

2. Run:
   ```
   /cost-guard:install-indicator
   ```

   If you already have a bottom-row command, cost-guard prints the two options and exits without modifying anything. Pick one:
   - `/cost-guard:install-indicator compose` — cost-guard wraps your existing command and appends its row below.
   - `/cost-guard:install-indicator replace` — cost-guard takes over; your command is backed up.

3. Restart Claude Code (or `/reload-plugins` if your version supports it). The bottom row now shows the cost-guard line (plus, in compose mode, your existing output above).

4. To remove:
   ```
   /cost-guard:uninstall-indicator
   ```

   Compose/replace backup is restored byte-for-byte; a solo install is simply removed.

---

## Test 7 — cold-start seeding from history

**Verifies:** `seed_from_history` populates the ledger from existing `~/.claude/projects/*/*.jsonl` on first install.

**Steps:**

1. Wipe the plugin data:
   ```bash
   rm -rf ~/.claude/plugins/data/cost-guard-inline
   ```

2. Start Claude Code via `--plugin-dir` as usual.

3. Run:
   ```
   /cost-guard:diag
   ```

   You should see:
   - `.seeded: N bytes` (marker file present)
   - `cost-ledger.jsonl: N bytes` (populated, probably non-zero if you used Claude Code recently)
   - Recent halt-log entries if any halts have fired this session

4. If `.seeded` or `cost-ledger.jsonl` are missing after the first `SessionStart`, run `/cost-guard:diag` and share the output — that points at exactly which path is wrong.

---

## After testing

Restore defaults:

```
/cost-guard:set-session-limit 10
/cost-guard:set-step-limit 2
/cost-guard:set-rate 0.5
/cost-guard:set-subagent-cap 8
/cost-guard:set-warn 7
/cost-guard:resume
```
