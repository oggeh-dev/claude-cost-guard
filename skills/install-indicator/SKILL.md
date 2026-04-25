---
description: Install cost-guard's bottom-row indicator. If a bottom-row command already exists, cost-guard asks whether to compose (wrap and augment) or replace it. Usage — /cost-guard:install-indicator [compose|replace].
allowed-tools: Bash(*"cost-guard" install-indicator*) Edit(~/.claude/settings.json) Read(~/.claude/settings.json)
---

# cost-guard: install bottom-row indicator

The user may pass `compose` or `replace` to pick a mode up front. Otherwise cost-guard detects whether a bottom-row command is already configured and, if so, shows the user the available choices.

Run the CLI:

!`CLAUDE_PLUGIN_DATA="${CLAUDE_PLUGIN_DATA}" CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}" "${CLAUDE_PLUGIN_ROOT}/bin/cost-guard" install-indicator $ARGUMENTS`

## What to do based on the output above

**If you see a line of the form `cost-guard:apply-statusline:<JSON>`** in the CLI output (this means the plugin sandbox blocked the direct settings.json write and has emitted a machine-readable directive for you to apply):

1. Parse the JSON value after the prefix `cost-guard:apply-statusline:`.
2. Read `~/.claude/settings.json`.
3. Use the Edit tool to set its top-level `statusLine` field to the parsed JSON value (replacing any existing `statusLine` field; if the JSON value is `null`, remove the `statusLine` field instead). Preserve all other top-level fields exactly.
4. After applying, tell the user the indicator is installed and to restart Claude Code (or reload settings) to see it.

**If the CLI output asks the user to choose between `compose` and `replace`** (a bottom-row command is already configured): pass the two re-run commands the CLI printed back to the user verbatim and stop. Do not modify settings.json.

**If the CLI output says the indicator is already installed and current**: tell the user nothing changed and stop.

**If the CLI reported any other error**: pass the error through to the user, mention `~/.claude/settings.json`, and stop.

Do not add any other commentary, summaries, or explanations beyond what is asked for above.
