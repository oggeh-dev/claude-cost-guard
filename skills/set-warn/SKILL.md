---
description: Update the cost-guard per-session amber-warn threshold in USD. Usage — /cost-guard:set-warn <USD> (e.g. 5 for $5). Must be below the session cap.
disable-model-invocation: true
---

# cost-guard: set per-session warn threshold

The user requested a new warn threshold of: **$ARGUMENTS** USD.

The CLI output is below:

!`CLAUDE_PLUGIN_DATA="${CLAUDE_PLUGIN_DATA}" CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}" "${CLAUDE_PLUGIN_ROOT}/bin/cost-guard" set-warn $ARGUMENTS`

Confirm the new value in a single short sentence. If the CLI reported an error, explain the error and note the minimum allowed value (0.05). Do not add other commentary.
