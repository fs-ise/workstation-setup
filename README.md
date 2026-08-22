<p align="center">
  <img src="docs/logo.png" alt="Workstation setup logo" width="300">
</p>

<div align="center">

# Workstation setup

[![Ansible CI](https://github.com/fs-ise/workstation-setup/actions/workflows/ansible-ci.yml/badge.svg)](https://github.com/fs-ise/workstation-setup/actions/workflows/ansible-ci.yml)

</div>

Documentation available at [https://fs-ise.github.io/workstation-setup/](https://fs-ise.github.io/workstation-setup/).

From the repository root, use the same main commands as a personal overlay:

```sh
make install  # Apply the desired workstation configuration
make update   # Update software, reapply configuration, and audit
make audit    # Audit the resulting workstation state
```

See [Install software](https://fs-ise.github.io/workstation-setup/install_software.html)
and [Update software](https://fs-ise.github.io/workstation-setup/update_software.html)
for prerequisites, behavior, and verification guidance.

> **Supported platform:** This repository is currently tested/supported on
> **Fedora Workstation 44 x86_64**. The main playbook checks the operating
> system, major version, and architecture before it changes the workstation.

## Configuration ownership

This shared repository installs applications, research and development capabilities, generic shell support, and conservative lab-wide defaults. Personal dotfiles, desktop ergonomics, shortcuts, application preferences, managed browser extensions, and machine-specific hardware configuration belong in a personal Ansible overlay. See [Personal overlays](https://fs-ise.github.io/workstation-setup/personal_overlays.html) for the ownership, update, audit, and secrets model.

Automated checks lint and syntax-check the complete Ansible setup and exercise a
container-safe subset twice for idempotence. See [the Ansible CI test guide](tests/README.md)
for coverage, limitations, and local reproduction commands.

## Acknowledgment

This project reflects major contributions by Carlo Tang.

## License

Unless otherwise noted, source code, Ansible roles, scripts, configuration,
and other software artifacts are distributed under the [MIT License](LICENSE).
Documentation under [`docs/`](docs/) is dedicated to the public domain under
[CC0 1.0 Universal](docs/LICENSE).

By contributing, you agree that your contributions are provided under the
license that applies to the files you change.
