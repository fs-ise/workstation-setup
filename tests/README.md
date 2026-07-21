# Ansible CI tests

The CI checks the complete Ansible setup statically and runs a deliberately small,
safe subset in a Fedora 43 container. The execution test runs the `baseline` role
with package installation, package removal, TeX Live, and Flathub disabled. It
exercises the role's Git configuration, asserts the result, runs the playbook a
second time, and requires `changed=0` in the second play recap.

## Run the checks locally

Install the Python and Galaxy dependencies, then run the static checks:

```sh
python3.12 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

ansible-galaxy collection install -r requirements.yml

yamllint .
ansible-lint

ansible-playbook \
  --syntax-check \
  -i tests/inventory/hosts.yml \
  playbooks/lab-stack.yml

ansible-playbook \
  --list-tasks \
  -i tests/inventory/hosts.yml \
  playbooks/lab-stack.yml
```

Run the same unprivileged Fedora container used by GitHub Actions:

```sh
docker run --rm \
  --volume "$PWD:/workspace:Z" \
  --workdir /workspace \
  fedora:43 \
  bash -lc 'dnf install -y ansible-core git python3-libdnf5 && ansible-galaxy collection install -r requirements.yml && tests/run-idempotence.sh'
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

- **Executed in Fedora:** the baseline role's global Git configuration and its
  resulting state. Package loops are loaded but intentionally empty.
- **Static validation only:** all roles in `playbooks/lab-stack.yml`, including
  package repositories, downloads, Docker and LanguageTool containers, Quarto,
  OCR, Chrome, VS Code, Teams for Linux, Thunderbird, and desktop configuration.
- **Future VM tests:** real package installation/removal, Flatpak and GUI behavior,
  GNOME sessions and dconf, Docker's systemd service, reboot behavior, VirtualBox
  kernel modules, hardware integration, and desktop-user ownership.

Syntax checking resolves every referenced role, task include, handler, and
installed collection without applying workstation changes. It cannot detect every
runtime-only missing variable or platform failure, so those remain candidates for
Fedora VM integration tests.
