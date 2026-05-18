.PHONY: lab-stack audit-packages

lab-stack:
	ansible-playbook -i inventory -K playbooks/lab-stack.yml

audit-packages:
	ansible-playbook -i inventory -K playbooks/audit-unmanaged-packages.yml
