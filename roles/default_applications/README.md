# Default applications

Configure centralized Fedora MIME-type and URL-scheme defaults after their
applications have been installed.

```sh
ansible-playbook -i inventory -K playbooks/lab-stack.yml --tags default_applications
```

Edit `default_applications_associations` in `defaults/main.yml` to add an
association. Add the application's verified desktop-entry basename, mark it
required or optional, and list the MIME types it handles. The role searches the
system, user, and Flatpak application directories. A missing required entry
fails clearly; a missing optional entry is skipped.

Fedora 44's Thunderbird RPM exports
`net.thunderbird.Thunderbird.desktop`. The association also retains
`org.mozilla.Thunderbird.desktop` for Flatpak and `thunderbird.desktop` for
older installations. Candidate order determines which entry is selected when
more than one is installed.

The role registers `.qmd` files as `text/x-quarto-markdown` in the user's MIME
database before selecting their default application. This explicit definition
keeps MIME recognition consistent on minimal Fedora installations.

::: {.callout-manual}
**🔧 Manual setup and configuration**

- Confirm an unfamiliar MIME type with `xdg-mime query filetype <file>` before
  adding it. Do not infer a MIME type from a filename extension.
- Confirm a desktop ID from the installed `.desktop` file, not its display name.
:::

::: {.callout-check}
**✅ Check**

```sh
xdg-mime query filetype example.qmd
xdg-mime query default text/x-quarto-markdown
xdg-mime query default application/pdf
xdg-mime query default x-scheme-handler/https
```
:::

## Best practices and useful links

- [Shared MIME-info specification](https://specifications.freedesktop.org/shared-mime-info-spec/latest/)
- [Desktop entry specification](https://specifications.freedesktop.org/desktop-entry-spec/latest/)
- [Default application specification](https://specifications.freedesktop.org/mime-apps-spec/latest/)
