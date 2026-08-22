# Obsidian role

Install the Obsidian desktop application from Flathub.

```sh
ansible-playbook -i inventory -K playbooks/lab-stack.yml --tags obsidian
```

The role uses the existing system-wide Flatpak and Flathub configuration from
the `baseline` role. It declares its Flatpak ownership in
`obsidian_managed_flatpak_packages`, separately from the DNF packages consumed
by the current package audit.

::: {.callout-check}
**✅ Check**

```sh
flatpak info md.obsidian.Obsidian
```
:::

## Best practices and useful links

- [Obsidian Help](https://help.obsidian.md/)
- [Obsidian on Flathub](https://flathub.org/apps/md.obsidian.Obsidian)
