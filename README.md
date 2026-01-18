# Workstation setup

## Preparation

Install Fedora

```sh
sudo dnf -y install git ansible-core python3-pip
ansible --version
git --version
```

Ansible collections

```sh
ansible-galaxy collection install community.general community.docker
```

## Install

```sh
git clone git@github.com:fs-ise/workstation-setup.git
cd workstation-setup

# copy host_vars/localhost.yml.example to host_vars/localhost.yml

ansible-playbook -K playbooks/lab-stack.yml

# upon dnf config-manager: command not found
sudo dnf -y install dnf-plugins-core
ansible-playbook -K playbooks/lab-stack.yml
```


## Test

```sh
git config --global user.name
git config --global user.email

docker version
docker run --rm hello-world

quarto --version
quarto check
```

Quarto test

```sh
mkdir -p ~/tmp-quarto-test && cd ~/tmp-quarto-test
cat > test.qmd <<'EOF'
---
title: "Lab Stack Test"
format: html
---

## It works

- Quarto: `r quarto::quarto_version()` (if R is installed)
- Docker: tested separately
- Git: configured
EOF

quarto render test.qmd
ls -la
```
