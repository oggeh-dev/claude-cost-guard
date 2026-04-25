---
description: Update the cost-guard per-step USD cap. A "step" is one full Claude response cycle (one user prompt → Claude's tool calls + final answer). Usage — /cost-guard:set-step-limit <USD>.
disable-model-invocation: true
---

# cost-guard: set per-step cost cap

The user requested a new per-step cap of: **$ARGUMENTS** USD.

The CLI output is below:

!`CLAUDE_PLUGIN_DATA="${CLAUDE_PLUGIN_DATA}" CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}" "${CLAUDE_PLUGIN_ROOT}/bin/cost-guard" set-step-limit $ARGUMENTS`

Confirm the new value to the user in a single short sentence. If the CLI reported an error, explain the error and note that the minimum allowed value is 0.05. Do not add any other commentary.
