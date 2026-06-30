# AGENTS.md

This repository provides workstation setup instructions and Ansible automation for preparing research, teaching, and lab workstations.

Agents working in this repository should prioritize clarity, reproducibility, and safe system changes. Documentation should make it easy for a new team member to understand what will be installed, what needs to be done manually, and how to verify that the setup worked.

## Repository purpose

The repository should help users:

- prepare a workstation for lab work,
- run Ansible playbooks for recurring setup tasks,
- understand which steps are automated and which remain manual,
- verify successful installation and configuration,
- find useful follow-up documentation.

Prefer practical, executable instructions over abstract explanations.

## Documentation standards

### General writing style

- Use clear, direct, instructional language.
- Prefer short sections with concrete commands.
- Avoid long prose when a checklist, command block, or table is clearer.
- Explain the purpose of each role or setup step before showing commands.
- Distinguish clearly between:
  - automated setup,
  - manual setup,
  - checks/verification,
  - optional configuration,
  - best practices and useful links.

### Structure for role documentation

Each role or setup section should follow this order:

1. Short purpose statement
2. Ansible command to run the role or tag
3. Manual setup and configuration, if needed
4. Check section
5. Best practices and useful links

Start each role section with the relevant Ansible instruction.

Use this pattern:

````md
## OCR tools

Install tools for optical character recognition and PDF processing.

```sh
ansible-playbook -i inventory -K playbooks/lab-stack.yml --tags ocr
`````

::: {.callout-manual}
**🔧 Manual setup and configuration**

* Add manual post-installation steps here, if required.
* Mention external accounts, GUI configuration, or credential setup here.
  :::

::: {.callout-check}
**✅ Check**

```sh
tesseract --version
ocrmypdf --version
```
:::

## Using OCR

For German and English documents, use:

```sh
ocrmypdf -l deu+eng input.pdf output.pdf
```

- For English-only documents, use:

```sh
ocrmypdf -l eng input.pdf output.pdf
```

## Best practices and useful links

* [OCRmyPDF documentation](https://ocrmypdf.readthedocs.io/)
* [Tesseract documentation](https://tesseract-ocr.github.io/)

`````
```

### Required callout types

Use Pandoc/Quarto-style callouts consistently.

#### Manual setup callout

Use this callout for anything that cannot or should not be fully automated, such as account registration, GitHub settings, SSH keys, GPG keys, GUI configuration, private credentials, or institution-specific steps.

````md
::: {.callout-manual}
**🔧 Manual setup and configuration**

- Set up SSH and register on GitHub

```sh
ssh-keygen -t ed25519 -a 64 -C "your-email@institution.edu"
ssh-add ~/.ssh/id_ed25519
cat ~/.ssh/id_ed25519.pub | wl-copy
# add in GitHub settings/ssh
```

- Set up GPG and register on GitHub ([instructions](https://docs.github.com/en/authentication/managing-commit-signature-verification/telling-git-about-your-signing-key))
:::
`````

#### Check callout

Use this callout for verification commands that users can run after installation.

````md
::: {.callout-check}
**✅ Check**

```sh
git config --global user.name
git config --global user.email

docker version
docker run --rm hello-world

ssh -V
ls -la ~/.ssh/*.pub 2>/dev/null || echo "No SSH public keys found"
ssh-add -l || true
ssh -T git@github.com
```
:::
````

### Ansible command standard

When documenting a role or tag, start with the command needed to run it.

Use this form:

```sh
ansible-playbook -i inventory -K playbooks/lab-stack.yml --tags <tag>
```

Example:

```sh
ansible-playbook -i inventory -K playbooks/lab-stack.yml --tags ocr
```

When multiple tags are relevant, prefer one concise command:

```sh
ansible-playbook -i inventory -K playbooks/lab-stack.yml --tags git,docker,ocr
```

Only use different inventory or playbook paths if the repository actually contains them and the surrounding documentation explains why.

### Command block standards

* Use fenced code blocks with language markers, especially `sh`, `yaml`, `md`, or `ini`.
* Prefer copy-pasteable commands.
* Do not include destructive commands unless clearly explained.
* Avoid commands that expose secrets, tokens, or private keys.
* For commands requiring sudo privileges through Ansible, use `-K`.
* Prefer idempotent commands where possible.

Good:

```sh
ansible-playbook -i inventory -K playbooks/lab-stack.yml --tags docker
```

Avoid:

```sh
sudo rm -rf ...
```

unless there is a strong reason and a warning is included.

## Ansible standards

### Roles and tags

* Each Ansible role should have a clear tag.
* The tag name should be short, lowercase, and descriptive.
* Documentation should use the same tag names as the playbooks.
* Keep role responsibilities focused. A role should not install unrelated tools.

Examples of good tag names:

```txt
git
docker
python
r
ocr
zotero
vscode
```

### Idempotency

Ansible tasks should be idempotent whenever possible.

Prefer Ansible modules over raw shell commands:

* Use `apt`, `package`, `file`, `copy`, `template`, `git`, `lineinfile`, or `blockinfile` where appropriate.
* Use `command` instead of `shell` when shell features are not needed.
* Use `changed_when` and `creates` where needed to avoid false changes.
* Avoid tasks that always report `changed` unless unavoidable.

### Variables

* Use variables for repeated values.
* Keep defaults close to the role when appropriate.
* Avoid hard-coding personal usernames, emails, local paths, or institution-specific assumptions.
* Do not commit secrets, tokens, private keys, or local credentials.

### Safety

Agents must not introduce tasks that:

* upload private keys,
* overwrite existing user configuration without backup or confirmation,
* install untrusted scripts using `curl | sh`,
* silently change Git identity,
* disable security features,
* remove large directories without explicit documentation.

When a potentially risky operation is necessary, document it clearly and provide a check or rollback hint.

## Markdown style

* Use sentence case for headings.
* Use descriptive headings, not vague labels like “Misc” or “Stuff”.
* Keep heading levels consistent.
* Prefer relative links for files in this repository.
* Use external links only when they point to stable, authoritative documentation.
* Keep tables small and readable.
* Use bullet lists for procedural notes and numbered lists for ordered procedures.

## Best practices and useful links sections

Each substantial role or setup page should end with a section named:

```md
## Best practices and useful links
```

This section should include:

* official documentation,
* relevant security guidance,
* troubleshooting references,
* project-specific notes,
* links to related roles or setup pages in this repository.

Example:

```md
## Best practices and useful links

- [GitHub SSH documentation](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
- [GitHub GPG signing documentation](https://docs.github.com/en/authentication/managing-commit-signature-verification)
- [Docker post-installation steps for Linux](https://docs.docker.com/engine/install/linux-postinstall/)
```

## Pull request expectations

Before finalizing changes, check that:

* documentation commands match actual playbook, inventory, and tag names,
* role documentation starts with the relevant `ansible-playbook` command,
* manual steps are placed in `::: {.callout-manual}` blocks,
* verification steps are placed in `::: {.callout-check}` blocks,
* each major setup section ends with best practices and useful links,
* code blocks have language identifiers,
* no secrets or local credentials are committed,
* changes are consistent with existing repository style.

## Preferred response style for agents

When proposing changes:

* briefly summarize what changed,
* mention affected files,
* list any checks that should be run,
* call out assumptions or unresolved questions.

When editing documentation, prefer a ready-to-commit patch over broad advice.
