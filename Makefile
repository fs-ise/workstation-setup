.PHONY: setup configure install update update-base audit lab-stack audit-packages backup

VORTA_APP_ID := com.borgbase.Vorta

setup:
	sudo dnf -y install ansible-core python3 python3-pip dnf-plugins-core
	ansible-galaxy collection install -r requirements.yml --upgrade

configure: setup
	$(MAKE) lab-stack

# Backward-compatible alias; use configure for new workflows.
install: configure

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
	sudo dnf upgrade --refresh
	flatpak update
	$(MAKE) configure

audit:
	$(MAKE) audit-packages

lab-stack:
	ansible-playbook -i inventory -K playbooks/lab-stack.yml

audit-packages:
	ansible-playbook -i inventory -K playbooks/audit-unmanaged-packages.yml

backup:
	@set -eu; \
	printf '%s\n' \
		'[TODO] nextcloud-sync-check: Verify that Nextcloud synchronization is complete.' \
		'[TODO] git-repo-check: Verify that local repositories have no uncommitted or unpushed changes.'; \
	if ! command -v flatpak >/dev/null 2>&1; then \
		echo "Vorta cannot be launched because Flatpak is not installed or is not on PATH." >&2; \
		exit 1; \
	fi; \
	if ! flatpak info "$(VORTA_APP_ID)" >/dev/null 2>&1; then \
		echo "Vorta is not installed. Install and configure $(VORTA_APP_ID) before running make backup." >&2; \
		exit 1; \
	fi; \
	echo "Vorta only opens the interface: start the configured backup and verify that it completes successfully."; \
	if flatpak ps --columns=application 2>/dev/null | awk '$$0 == "$(VORTA_APP_ID)" { found = 1 } END { exit !found }'; then \
		echo "Vorta is already running; not launching another instance."; \
	else \
		flatpak run "$(VORTA_APP_ID)"; \
	fi
