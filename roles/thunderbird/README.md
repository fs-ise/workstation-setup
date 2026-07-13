# Thunderbird role

Installs Thunderbird and manages a curated Thunderbird extension policy.

```sh
ansible-playbook -i inventory -K playbooks/lab-stack.yml --tags thunderbird
```

The role writes system-wide Enterprise Policies to `/etc/thunderbird/policies/policies.json` and uses `ExtensionSettings`, not the older `Extensions` policy. Curated extensions use `installation_mode: normal_installed`, not `force_installed`, so Thunderbird installs them automatically while still allowing users to disable them.

## Variables

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

To remove a sensitive extension such as Thunderbird MCP, override `thunderbird_extensions` and omit that entry. To disable all extension policy management, set:

```yaml
thunderbird_extensions_enabled: false
```

## Policy behavior

If `/etc/thunderbird/policies/policies.json` already exists, the role preserves unrelated policy settings and merges the managed `ExtensionSettings` entries into the existing policy structure. Restart Thunderbird after policy changes so Thunderbird can apply them.
