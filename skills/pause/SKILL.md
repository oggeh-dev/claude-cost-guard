---
description: Pause cost-guard halting. Default is global. Pass a session id to pause only that session.
disable-model-invocation: true
---

# cost-guard: pause halts

The CLI output is below:

!`CLAUDE_PLUGIN_DATA="${CLAUDE_PLUGIN_DATA}" CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}" "${CLAUDE_PLUGIN_ROOT}/bin/cost-guard" pause`

Confirm to the user that cost-guard has been disabled, in one short sentence. Warn them that their runaway-cost protection is now off and tell them to run `/cost-guard:resume` to turn it back on. Do not add any other commentary.
