.PHONY: update lab-stack audit-packages

update:
	git pull --ff-only
	sudo dnf upgrade --refresh
	flatpak update
	$(MAKE) lab-stack
	$(MAKE) audit-packages

lab-stack:
	ansible-playbook -i inventory -K playbooks/lab-stack.yml

audit-packages:
	ansible-playbook -i inventory -K playbooks/audit-unmanaged-packages.yml
