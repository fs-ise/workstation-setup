.PHONY: deps install update update-base audit lab-stack audit-packages

deps:
	ansible-galaxy collection install -r requirements.yml --upgrade

install:
	$(MAKE) lab-stack

update:
	$(MAKE) update-base
	$(MAKE) audit

update-base:
	@if git symbolic-ref -q HEAD >/dev/null; then \
		git pull --ff-only; \
	else \
		status=$$?; \
		if [ "$$status" -eq 1 ]; then \
			echo "Skipping Git update: checkout is detached (for example, at a release tag)."; \
		else \
			exit "$$status"; \
		fi; \
	fi
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
