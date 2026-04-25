---
description: Show current cost-guard budget, 5-hour slot percentage, burn rate, and limits.
disable-model-invocation: true
---

# cost-guard status

The output below was produced by running `cost-guard status`:

!`CLAUDE_PLUGIN_DATA="${CLAUDE_PLUGIN_DATA}" CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}" "${CLAUDE_PLUGIN_ROOT}/bin/cost-guard" status`

Summarize the status above for the user in one short paragraph. Call out clearly:
- whether cost-guard is enabled
- current 5-hour slot percentage and whether it is under, at, or over the configured budget
- current burn rate in USD/min and whether it is under or over the configured limit
- time until the 5-hour slot resets

Do not add any other commentary. Do not offer to change settings unless the user asks.
