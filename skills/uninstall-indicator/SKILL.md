---
description: Remove cost-guard's bottom-row indicator. If a previous command was backed up at install time, it is restored byte-for-byte.
disable-model-invocation: true
---

# cost-guard: uninstall bottom-row indicator

The CLI output is below:

!`CLAUDE_PLUGIN_DATA="${CLAUDE_PLUGIN_DATA}" CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}" "${CLAUDE_PLUGIN_ROOT}/bin/cost-guard" uninstall-indicator`

Summarize the outcome in one short sentence:

- **If a previous command was restored**: tell the user their prior bottom-row command is active again after next restart.
- **If nothing was installed**: tell the user there was nothing to remove.
- **If the indicator was removed without a backup**: say the bottom row is now empty and they can set their own command via `~/.claude/settings.json` or `/statusline`.
- **If the CLI reported an error**: pass it through.

Cost-guard's halts keep working regardless — only the live indicator is affected.

Do not add other commentary.
