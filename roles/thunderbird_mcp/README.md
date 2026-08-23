# Thunderbird MCP role

Installs the pinned Thunderbird MCP bridge with Fedora's versioned Node.js 22 runtime and merges its `normal_installed` extension entry into the existing Thunderbird Enterprise Policies document. The role preserves unrelated policies and extensions.

The integration exposes sensitive local mail data and is enabled by default for full playbook runs. Set `thunderbird_mcp_enabled: false` to disable it. Optional client configuration is controlled by `thunderbird_mcp_write_client_fragment` and is written with mode `0600`.

Key defaults retain the established `thunderbird_mcp_*` names, release `0.7.4`, upstream repository, installation directory, extension ID, and XPI URL.
