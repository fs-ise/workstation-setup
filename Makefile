.PHONY: lab-stack

lab-stack:
	ansible-playbook -K playbooks/lab-stack.yml
