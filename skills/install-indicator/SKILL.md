---
description: Install cost-guard's bottom-row indicator. If a bottom-row command already exists, cost-guard asks whether to compose (wrap and augment) or replace it. Usage — /cost-guard:install-indicator [compose|replace].
disable-model-invocation: true
---

# cost-guard: install bottom-row indicator

The user may pass `compose` or `replace` to pick a mode up front. Otherwise cost-guard detects whether a bottom-row command is already configured and, if so, shows the user the available choices.

The CLI output is below:

!`CLAUDE_PLUGIN_DATA="${CLAUDE_PLUGIN_DATA}" CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}" "${CLAUDE_PLUGIN_ROOT}/bin/cost-guard" install-indicator $ARGUMENTS`

Summarize the outcome for the user in a single short message:

- **If the CLI presented choices** (a bottom-row command is already configured): tell the user to pick `compose` (keep their existing command and add cost-guard's row below it) or `replace` (cost-guard takes over; existing is backed up for later restore). Repeat the exact two re-run commands the CLI printed.
- **If the indicator was installed (either compose or replace)**: tell the user to restart Claude Code or reload settings to see the change, and that `/cost-guard:uninstall-indicator` will revert it.
- **If the indicator was already installed**: say so and note that nothing changed.
- **If the CLI reported an error**: pass the error through and point at `~/.claude/settings.json`.

Do not add any other commentary.
