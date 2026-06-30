# Workstation setup

See the [docs](https://fs-ise.github.io/workstation-setup/).

## Run the main workstation setup

```sh
make lab-stack
```

Equivalent explicit command:

```sh
ansible-playbook -i inventory -K playbooks/lab-stack.yml
```

## Audit unmanaged Fedora/DNF packages

See documentation: [Update software](docs/update_software.qmd).

## Acknowledgment

This project reflects major contributions by Carlo Tang.

## License

This project is distributed under the [MIT License](LICENSE) the documentation is distributed under the [CC-0](https://creativecommons.org/publicdomain/zero/1.0/) license.
If you contribute to the project, you agree to share your contribution following these licenses.
