---
description: Update the cost-guard per-session USD cap. Usage — /cost-guard:set-session-limit <USD> (e.g. 15 for $15).
disable-model-invocation: true
---

# cost-guard: set per-session cost cap

The user requested a new session cap of: **$ARGUMENTS** USD.

The CLI output is below:

!`CLAUDE_PLUGIN_DATA="${CLAUDE_PLUGIN_DATA}" CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}" "${CLAUDE_PLUGIN_ROOT}/bin/cost-guard" set-session-limit $ARGUMENTS`

Confirm the new value to the user in a single short sentence. If the CLI reported an error, explain the error and note that the minimum allowed value is 0.10. Do not add any other commentary.
