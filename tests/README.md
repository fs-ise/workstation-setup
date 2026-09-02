# Ansible CI tests

The CI checks the complete Ansible setup statically and runs a deliberately small,
safe subset in a Fedora 44 x86_64 container, matching the repository's supported
platform. The execution test runs the `baseline`, `desktop_apps`,
`borg_vorta`, and `keepassxc` roles with package installation, TeX Live, and
Flathub disabled. Desktop cleanup uses a deliberately absent fixture package
to verify DNF's idempotent `state: absent` behavior. It
also runs `default_applications` with a reduced fixture and a fake desktop entry,
without installing GUI software. It asserts the Git and MIME configuration, runs
the playbook a second time, and requires `changed=0` in the second play recap.

## Run the checks locally

Install the Python and Galaxy dependencies, then run the static checks:

```sh
python3.12 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

make deps

python -m unittest discover -s tests -p 'test_*.py'

yamllint .
ansible-lint

ansible-playbook \
  --syntax-check \
  -i tests/inventory/hosts.yml \
  playbooks/lab-stack.yml

ansible-playbook \
  --syntax-check \
  -i tests/inventory/hosts.yml \
  playbooks/cloud-stack.yml

ansible-playbook \
  --syntax-check \
  -i tests/inventory/hosts.yml \
  playbooks/audit-unmanaged-packages.yml

ansible-playbook \
  -i tests/inventory/hosts.yml \
  tests/playbooks/package-audit-derivation.yml

ansible-playbook \
  -i localhost, \
  tests/playbooks/preflight.yml

ansible-playbook \
  --list-tasks \
  -i tests/inventory/hosts.yml \
  playbooks/lab-stack.yml
```

The `unittest discover` command is the canonical way to run the repository's
full Python test suite, both locally and in CI. It automatically includes every
`tests/test_*.py` module.

Run the same unprivileged Fedora container used by GitHub Actions:

```sh
docker run --rm \
  --volume "$PWD:/workspace:Z" \
  --workdir /workspace \
  fedora:44 \
  bash -lc 'dnf install -y ansible-core git make python3-libdnf5 && make deps && tests/run-idempotence.sh'
```

The container is not privileged. All changes are confined to its disposable
filesystem and the ignored `tests/output/` directory in the mounted checkout.
## Extend execution coverage

Add a role to `tests/playbooks/ci.yml`, override its package or service variables
with container-safe values, add an assertion, and confirm that the second run has
no changes. Prefer a role variable that defaults to the existing workstation
behavior when only part of a role is unsafe. Tag indivisible tasks with `ci_skip`,
`gui`, `hardware`, or `requires_systemd`, and document why the test playbook skips
the tag. Do not mark mutating commands unchanged merely to satisfy the test.

## Coverage and limitations

- **Executed in Fedora:** the baseline role's global Git configuration, the
  `borg_vorta` role with Borg and Vorta installation disabled, the KeePassXC
  role with its package list intentionally empty, and the
  default-applications role's Fedora Quarto MIME recognition, legacy association
  cleanup, desktop-entry validation, optional-application skip, `mimeapps.list`
  updates, and queries. Package loops are loaded but intentionally empty.
- **Static validation only:** all roles in `playbooks/lab-stack.yml`, including
  package repositories, downloads, Docker and LanguageTool containers, Quarto's
  official RPM download and installation,
  OCR, Chrome, VS Code, Teams for Linux, Thunderbird, and desktop configuration.
- **Future VM tests:** real package installation/removal, Flatpak and GUI behavior,
  GNOME sessions and dconf, Docker's systemd service, reboot behavior, VirtualBox
  kernel modules, hardware integration, and desktop-user ownership.

The VeraCrypt test playbook separately exercises supported and unsupported platform decisions, pinned security settings, upgrade/no-downgrade decisions, and a repeated decision without downloading the RPM.

Syntax checking resolves every referenced role, task include, handler, and
installed collection without applying workstation changes. It cannot detect every
runtime-only missing variable or platform failure, so those remain candidates for
Fedora VM integration tests.
