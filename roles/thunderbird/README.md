# Thunderbird role

Installs Thunderbird, manages a curated Thunderbird extension policy, and provisions `thunderbird-cli` with its local bridge service.

```sh
ansible-playbook -i inventory -K playbooks/lab-stack.yml --tags thunderbird
```

The role:

- installs Thunderbird through DNF, with a Flatpak fallback;
- installs pinned `thunderbird-cli` and `thunderbird-cli-bridge` npm packages under the target user's `~/.local` directory;
- installs and starts the system-level `thunderbird-cli-bridge` service as the target user;
- installs the signed Thunderbird AI Bridge extension through Enterprise Policies; and
- manages the remaining curated Thunderbird extensions.

The role writes system-wide Enterprise Policies to `/etc/thunderbird/policies/policies.json` and uses `ExtensionSettings`, not the older `Extensions` policy. Curated extensions use `installation_mode: normal_installed`, not `force_installed`, so Thunderbird installs them automatically while still allowing users to disable them.

## Verify thunderbird-cli

Restart Thunderbird after running the role, then check:

```sh
systemctl status thunderbird-cli-bridge
~/.local/bin/tb bridge-status
~/.local/bin/tb health
```

`bridge-status` verifies the daemon. `health` also requires Thunderbird to be running and the Thunderbird AI Bridge extension to be connected.

## Variables

- `thunderbird_cli_enabled`: set to `false` to skip CLI, bridge, and service provisioning.
- `thunderbird_cli_version`: npm/release version to install.
- `thunderbird_cli_extension_version`: signed extension version included in the selected release.
- `thunderbird_cli_npm_prefix`: installation prefix; defaults to the target user's `~/.local` directory.
- `thunderbird_cli_npm_packages`: npm packages installed for the CLI and bridge.
- `thunderbird_extensions_enabled`: set to `false` to stop this role from managing extension policy.
- `thunderbird_extensions`: list of extension records. Each record should include:
  - `name`
  - `id`
  - `install_url`
  - `comment`

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

To remove a sensitive extension from newly generated defaults, override `thunderbird_extensions` and omit that entry. Existing entries in `/etc/thunderbird/policies/policies.json` are preserved by the merge logic and must be removed explicitly if they are no longer wanted. To disable all extension policy management, set:

```yaml
thunderbird_extensions_enabled: false
```

The Thunderbird AI Bridge and Thunderbird MCP extensions can read or modify email. Enable them only on trusted workstations and review their permissions and local service configuration.

## Policy behavior

If `/etc/thunderbird/policies/policies.json` already exists, the role preserves unrelated policy settings and merges the managed `ExtensionSettings` entries into the existing policy structure. Restart Thunderbird after policy changes so Thunderbird can apply them.
