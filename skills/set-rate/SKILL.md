---
description: Update the cost-guard per-minute cost limit in USD/min. Usage — /cost-guard:set-rate <USD/min>.
disable-model-invocation: true
---

# cost-guard: set per-minute cost limit

The user requested a new rate limit of: **$ARGUMENTS** USD/min.

The CLI output is below:

!`CLAUDE_PLUGIN_DATA="${CLAUDE_PLUGIN_DATA}" CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}" "${CLAUDE_PLUGIN_ROOT}/bin/cost-guard" set-rate $ARGUMENTS`

Confirm the new value to the user in a single short sentence. If the CLI reported an error, explain the error and state the minimum allowed value (0.01). Do not add any other commentary.
