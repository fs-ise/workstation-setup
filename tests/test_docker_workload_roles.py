import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DockerWorkloadRoleTests(unittest.TestCase):
    @staticmethod
    def task_block(tasks, name):
        block = tasks.split(f"- name: {name}\n", 1)[1]
        return block.split("\n- name:", 1)[0]

    def test_docker_conflict_removal_surfaces_dnf_failures(self):
        tasks = (ROOT / "roles/docker/tasks/main.yml").read_text(encoding="utf-8")
        removal = self.task_block(
            tasks, "Remove podman-docker (conflicts with Docker CE CLI)"
        )
        self.assertIn("ansible.builtin.dnf:", removal)
        self.assertIn("name: podman-docker", removal)
        self.assertIn("state: absent", removal)
        self.assertNotIn("failed_when", removal)
        self.assertNotIn("ignore_errors", removal)

    def test_docker_repository_enforces_signature_verification(self):
        defaults = (ROOT / "roles/docker/defaults/main.yml").read_text(encoding="utf-8")
        tasks = (ROOT / "roles/docker/tasks/main.yml").read_text(encoding="utf-8")
        self.assertIn("ansible.builtin.rpm_key:", tasks)
        self.assertIn("ansible.builtin.yum_repository:", tasks)
        self.assertIn("gpgcheck: true", tasks)
        self.assertIn("disable_gpg_check: false", tasks)
        self.assertNotIn("disable_gpg_check: true", tasks)
        self.assertIn("docker_rpm_signing_key_fingerprint:", defaults)
        self.assertIn("download.docker.com/linux/fedora", defaults)

    def test_all_docker_engine_packages_use_the_verified_install_task(self):
        defaults = (ROOT / "roles/docker/defaults/main.yml").read_text(encoding="utf-8")
        tasks = (ROOT / "roles/docker/tasks/main.yml").read_text(encoding="utf-8")
        for package in (
            "docker-ce",
            "docker-ce-cli",
            "containerd.io",
            "docker-buildx-plugin",
            "docker-compose-plugin",
        ):
            self.assertIn(f"  - {package}", defaults)
        self.assertIn('name: "{{ docker_packages }}"', tasks)

    def test_docker_role_contains_only_engine_configuration(self):
        docker_files = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (ROOT / "roles/docker").rglob("*.yml")
        )
        for image in (
            "grobid/grobid",
            "jbarlow83/ocrmypdf",
            "rocker/tidyverse",
            "rocker/verse",
            "python:3",
            "alekzonder/puppeteer",
        ):
            self.assertNotIn(image, docker_files)

    def test_grobid_keeps_its_pinned_image(self):
        defaults = (ROOT / "roles/grobid/defaults/main.yml").read_text(encoding="utf-8")
        self.assertIn('grobid_version: "0.9.0"', defaults)
        self.assertIn('grobid_image: "grobid/grobid:{{ grobid_version }}-full"', defaults)

    def test_grobid_container_lifecycle_is_declarative(self):
        tasks = (ROOT / "roles/grobid/tasks/main.yml").read_text(encoding="utf-8")
        container = self.task_block(tasks, "Ensure GROBID container is started")

        self.assertIn("community.docker.docker_container:", container)
        self.assertIn('name: "{{ grobid_container_name }}"', container)
        self.assertIn('image: "{{ grobid_image }}"', container)
        self.assertIn("state: started", container)
        self.assertIn("pull: missing", container)
        self.assertIn("restart_policy: unless-stopped", container)
        self.assertIn('- "{{ grobid_port }}:8070"', container)
        self.assertNotIn("recreate: true", container)

        for imperative_command in (
            "docker container inspect",
            "docker run",
            "docker start",
        ):
            self.assertNotIn(imperative_command, tasks)

    def test_container_roles_depend_on_docker(self):
        for role in ("grobid", "languagetool", "ocr_containers", "development_containers"):
            metadata = (ROOT / f"roles/{role}/meta/main.yml").read_text(encoding="utf-8")
            self.assertIn("dependencies:\n  - role: docker", metadata)

    def test_optional_image_roles_use_never_tag(self):
        play = (ROOT / "playbooks/lab-stack.yml").read_text(encoding="utf-8")
        for role in ("ocr_containers", "development_containers"):
            stanza = f"- role: {role}\n      tags: [never, {role}]"
            self.assertIn(stanza, play)

    def test_r_uses_local_installation_exclusively(self):
        play = (ROOT / "playbooks/lab-stack.yml").read_text(encoding="utf-8")
        self.assertNotIn("- role: r_containers", play)
        self.assertFalse((ROOT / "roles/r_containers").exists())


if __name__ == "__main__":
    unittest.main()
