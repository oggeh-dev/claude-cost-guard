---
description: Update the cost-guard subagent-spawn cap per step. Usage — /cost-guard:set-subagent-cap <N> where N is 1 to 100.
disable-model-invocation: true
---

# cost-guard: set per-step subagent cap

The user requested a new subagent cap of: **$ARGUMENTS**

The CLI output is below:

!`CLAUDE_PLUGIN_DATA="${CLAUDE_PLUGIN_DATA}" CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}" "${CLAUDE_PLUGIN_ROOT}/bin/cost-guard" set-subagent-cap $ARGUMENTS`

Confirm the new value in a single short sentence. If the CLI reported an error, explain the error and list the valid range (1 to 100). Do not add other commentary.
