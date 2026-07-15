# Thunderbird role

Installs Thunderbird, manages a curated Thunderbird extension policy, and can install the local Thunderbird MCP bridge for MCP clients.

```sh
ansible-playbook -i inventory -K playbooks/lab-stack.yml --tags thunderbird
```

The role writes system-wide Enterprise Policies to `/etc/thunderbird/policies/policies.json` and uses `ExtensionSettings`, not the older `Extensions` policy. Curated extensions use `installation_mode: normal_installed`, not `force_installed`, so Thunderbird installs them automatically while still allowing users to disable them. Restart Thunderbird after the first policy run so Thunderbird can install the managed extensions.

## Variables

- `thunderbird_extensions_enabled`: set to `false` to stop this role from managing extension policy.
- `thunderbird_extensions`: list of extension records. Each record should include:
  - `name`
  - `id`
  - `install_url`
  - `comment`
- `thunderbird_mcp_enabled`: set to `false` to omit Thunderbird MCP from the default managed extension list and skip bridge installation.
- `thunderbird_mcp_version`: pinned Thunderbird MCP release. The default is `0.7.4`.
- `thunderbird_mcp_install_dir`: system checkout for the MCP bridge. The default is `/opt/thunderbird-mcp`.
- `thunderbird_mcp_write_client_fragment`: set to `true` to write an MCP client configuration fragment. The default is `false`.
- `thunderbird_mcp_client_fragment_dir`: directory for the optional user-owned fragment. The default is `{{ target_home }}/.config/workstation-setup/mcp`.

## Thunderbird MCP extension and bridge

When `thunderbird_mcp_enabled` is `true`, the role installs two Thunderbird MCP pieces reproducibly:

- the Thunderbird extension through Enterprise Policies, using the verified extension ID `thunderbird-mcp@tkasperczyk.dev` and the pinned bootstrap XPI for `v{{ thunderbird_mcp_version }}`;
- the Node.js MCP bridge from `https://github.com/TKasperczyk/thunderbird-mcp.git`, checked out at Git tag `v{{ thunderbird_mcp_version }}` in `{{ thunderbird_mcp_install_dir }}`.

The role installs `git` and `nodejs` for the bridge. It does not run `npm install` because the bridge currently does not require a runtime dependency installation step. It also does not copy `connection.json` or session tokens; the bridge discovers the active extension connection dynamically while Thunderbird is running.

Extension releases from `v0.7.3` onward can update through Thunderbird after this pinned bootstrap installation. Automatic updates still depend on Thunderbird's add-on update settings and continued trust in the upstream update channel.

The bridge command for MCP clients is:

```sh
node /opt/thunderbird-mcp/mcp-bridge.cjs
```

Use `{{ thunderbird_mcp_install_dir }}/mcp-bridge.cjs` instead if you override the installation directory.

::: {.callout-manual}
**🔧 Manual setup and configuration**

- Restart Thunderbird after the initial Enterprise Policy installation.
- Keep Thunderbird running when an MCP client calls the bridge; bridge calls can reach the extension only while Thunderbird is active.
- Review Thunderbird MCP account access, enabled tools, and send-safety settings inside Thunderbird before connecting an MCP client.
- Treat Thunderbird MCP as sensitive access. It can expose email, contacts, calendars, filters, and message-management operations to local MCP clients.
- Merge the optional MCP client fragment into your chosen MCP client manually. This role does not modify `~/.claude.json`, Codex configuration, or any other live client configuration automatically.
:::

## Optional MCP client configuration fragment

Set this variable to write a user-owned, disabled-by-default MCP server configuration fragment:

```yaml
thunderbird_mcp_write_client_fragment: true
```

The fragment is written to:

```text
~/.config/workstation-setup/mcp/thunderbird-mail.json
```

It contains the configured bridge path, for example:

```json
{
  "mcpServers": {
    "thunderbird-mail": {
      "command": "node",
      "args": ["/opt/thunderbird-mcp/mcp-bridge.cjs"]
    }
  }
}
```

Copy or merge the `mcpServers.thunderbird-mail` object into the configuration file used by your MCP client, then restart or reload that client.

## Add or override extensions

Override `thunderbird_extensions` in inventory or group variables. Resolve each extension ID from the XPI manifest or authoritative add-on metadata; do not infer IDs from display names.

```yaml
thunderbird_extensions:
  - name: Example extension
    id: example@example.org
    install_url: https://example.org/example.xpi
    comment: Explain why this extension is installed.
```

## Disable sensitive extensions

To disable the default Thunderbird MCP automation, set:

```yaml
thunderbird_mcp_enabled: false
```

That setting skips bridge installation and omits Thunderbird MCP from the role's default managed extension list while leaving unrelated Thunderbird extensions unchanged. The role does not delete an existing user installation or remove unrelated policy entries automatically.

To disable all extension policy management, set:

```yaml
thunderbird_extensions_enabled: false
```

## Policy behavior

If `/etc/thunderbird/policies/policies.json` already exists, the role preserves unrelated policy settings and merges the managed `ExtensionSettings` entries into the existing policy structure. Restart Thunderbird after policy changes so Thunderbird can apply them.

::: {.callout-check}
**✅ Check**

```sh
thunderbird --version
node --version
git -C /opt/thunderbird-mcp describe --tags --exact-match
node /opt/thunderbird-mcp/mcp-bridge.cjs --help
python3 -m json.tool ~/.config/workstation-setup/mcp/thunderbird-mail.json >/dev/null
```
:::

## Best practices and useful links

- [Thunderbird Enterprise Policies](https://mozilla.github.io/policy-templates/)
- [Thunderbird add-ons](https://addons.thunderbird.net/)
- [Thunderbird MCP project](https://github.com/TKasperczyk/thunderbird-mcp)
