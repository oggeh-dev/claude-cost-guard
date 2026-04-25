---
description: Dump cost-guard's plugin state — file sizes, env vars, recent halts, effective config, and the current bottom-row command. For debugging only.
disable-model-invocation: true
---

# cost-guard: diagnostics

The CLI output is below:

!`CLAUDE_PLUGIN_DATA="${CLAUDE_PLUGIN_DATA}" CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}" "${CLAUDE_PLUGIN_ROOT}/bin/cost-guard" diag`

Present the diagnostic output to the user verbatim inside a code block so they can read every line. Do not summarize, do not rewrite. If any file is reported as `MISSING`, that is often the actual signal the user is looking for.

Do not add other commentary.
