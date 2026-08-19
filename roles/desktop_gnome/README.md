# Desktop GNOME role

Configure GNOME desktop applications, preferences, shortcuts, and selected
workstation connection settings.

```sh
ansible-playbook -i inventory -K playbooks/lab-stack.yml --tags desktop_gnome
```

The role registers separate GNOME custom keyboard shortcuts for `Ctrl+Alt+T`
and `Super+T`. Both run `ptyxis --new-window`, so each activation opens a new
window instead of only activating an existing Ptyxis process. Existing custom
shortcut paths remain registered when the role adds the two Ptyxis paths.

The role defaults `desktop_gnome_configure_wifionice_permanent_mac` to `true`.
When an existing NetworkManager profile named `WIFIonICE` is present, the role
sets that profile to use the device's permanent MAC address. ICE captive portals
may fail when a randomized or stable MAC address is used. Set the variable to
`false` to disable this behavior.

This setting affects only `WIFIonICE`; it does not globally disable
NetworkManager MAC-address privacy. The role does not disconnect or reconnect
Wi-Fi, so the change takes effect the next time the profile reconnects.

::: {.callout-manual}
**🔧 Manual setup and configuration**

- Create or connect to the `WIFIonICE` profile before running the role. If the
  profile does not exist yet, the role safely skips the change.
- Reconnect to `WIFIonICE` when convenient to apply a changed setting.
:::

::: {.callout-check}
**✅ Check**

```sh
nmcli --get-values 802-11-wireless.cloned-mac-address connection show WIFIonICE
# Expected output: permanent

dconf read /org/gnome/settings-daemon/plugins/media-keys/custom-keybindings
dconf read /org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/binding
dconf read /org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/command
dconf read /org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/ptyxis-super-t/binding
dconf read /org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/ptyxis-super-t/command
```
:::

## Best practices and useful links

- [NetworkManager `nm-settings-nmcli` reference](https://networkmanager.dev/docs/api/latest/nm-settings-nmcli.html)
- [NetworkManager Wi-Fi settings reference](https://networkmanager.dev/docs/api/latest/settings-802-11-wireless.html)
- [Ptyxis source and documentation](https://gitlab.gnome.org/chergert/ptyxis)
- [GNOME custom keybindings schema](https://gitlab.gnome.org/GNOME/gsettings-desktop-schemas/-/blob/master/schemas/org.gnome.desktop.wm.keybindings.gschema.xml.in)
