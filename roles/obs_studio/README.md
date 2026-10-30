# OBS Studio role

Install OBS Studio and its Background Removal plugin from Flathub as user-level
Flatpaks. The role ensures the user Flathub remote exists and independently
verifies both application IDs. It does not change OBS scenes, profiles, or
configuration.

The role checks exact application IDs before installing OBS. The
`community.general.flatpak` module currently matches installed IDs by substring;
because the plugin ID begins with the OBS ID, a plugin-only installation can
otherwise be mistaken for OBS Studio.

```bash
ansible-playbook -i inventory -K playbooks/lab-stack.yml --tags obs

flatpak info --user com.obsproject.Studio
flatpak info --user com.obsproject.Studio.Plugin.BackgroundRemoval

flatpak run --user com.obsproject.Studio
```

::: {.callout-manual}
**🔧 Manual setup and configuration**

- In OBS, select **Video Capture Device → Filters → Effect Filters → Background Removal** to enable the filter.
:::

::: {.callout-check}
**✅ Check**

```bash
flatpak info --user com.obsproject.Studio
flatpak info --user com.obsproject.Studio.Plugin.BackgroundRemoval
```
:::

## Best practices and useful links

- [OBS Studio](https://obsproject.com/)
- [OBS Studio on Flathub](https://flathub.org/apps/com.obsproject.Studio)
- [Background Removal plugin on Flathub](https://flathub.org/apps/com.obsproject.Studio.Plugin.BackgroundRemoval)
