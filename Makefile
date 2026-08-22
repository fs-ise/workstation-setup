.PHONY: deps install update update-base audit lab-stack audit-packages

deps:
	ansible-galaxy collection install -r requirements.yml --upgrade

install:
	$(MAKE) lab-stack

update:
	$(MAKE) update-base
	$(MAKE) audit

update-base:
	git pull --ff-only
	$(MAKE) deps
	sudo dnf upgrade --refresh
	flatpak update
	$(MAKE) install

audit:
	$(MAKE) audit-packages

lab-stack:
	ansible-playbook -i inventory -K playbooks/lab-stack.yml

audit-packages:
	ansible-playbook -i inventory -K playbooks/audit-unmanaged-packages.yml
