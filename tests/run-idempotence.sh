#!/usr/bin/env bash
set -euo pipefail

readonly inventory=tests/inventory/hosts.yml
readonly playbook=tests/playbooks/ci.yml
readonly output_dir=tests/output

rm -rf "${output_dir}"
mkdir -p "${output_dir}"


ansible-playbook -i "${inventory}" "${playbook}" | tee "${output_dir}/first-run.log"
ansible-playbook -i "${inventory}" "${playbook}" | tee "${output_dir}/second-run.log"

if ! sed -n '/PLAY RECAP/,$p' "${output_dir}/second-run.log" | grep -Eq 'changed=0([[:space:]]|$)'; then
  echo "The second Ansible run was not idempotent." >&2
  exit 1
fi
