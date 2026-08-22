.PHONY: deps update update-base lab-stack audit-packages

deps:
	ansible-galaxy collection install -r requirements.yml --upgrade

update:
	$(MAKE) update-base
	$(MAKE) audit-packages

update-base:
	git pull --ff-only
	$(MAKE) deps
	sudo dnf upgrade --refresh
	flatpak update
	$(MAKE) lab-stack

lab-stack:
	ansible-playbook -i inventory -K playbooks/lab-stack.yml

audit-packages:
	ansible-playbook -i inventory -K playbooks/audit-unmanaged-packages.yml
