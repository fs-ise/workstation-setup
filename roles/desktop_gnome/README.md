# Desktop GNOME role

Install reusable GNOME workstation applications and provide support for a
lab-managed list of GNOME Shell extensions. Personal desktop preferences,
keyboard shortcuts, and network profiles belong in a personal overlay.

```sh
ansible-playbook -i inventory -K playbooks/lab-stack.yml --tags desktop_gnome
```

By default, `desktop_gnome_shell_extensions` is empty. Lab deployments can add
extensions as dictionaries containing `name`, `uuid`, and `repo`; the role
installs and enables those extensions without replacing other enabled extension
UUIDs. The role also installs Obsidian and the generic GNOME configuration
dependencies used by the shared workstation stack.

::: {.callout-check}
**✅ Check**

```sh
flatpak info md.obsidian.Obsidian
dconf read /org/gnome/shell/disable-user-extensions
dconf read /org/gnome/shell/enabled-extensions
```
:::

## Best practices and useful links

- [GNOME Shell extensions](https://extensions.gnome.org/)
- [GNOME Shell extensions source](https://gitlab.gnome.org/GNOME/gnome-shell-extensions)
- [Ansible dconf module](https://docs.ansible.com/ansible/latest/collections/community/general/dconf_module.html)
- [Obsidian help](https://help.obsidian.md/)
