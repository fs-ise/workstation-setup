import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class WhisperRoleTests(unittest.TestCase):
    def setUp(self):
        self.defaults = yaml.safe_load(
            (ROOT / "roles/whisper/defaults/main.yml").read_text(encoding="utf-8")
        )
        self.tasks = yaml.safe_load(
            (ROOT / "roles/whisper/tasks/main.yml").read_text(encoding="utf-8")
        )

    def test_whisper_uses_expected_image_and_validated_persistent_model(self):
        self.assertEqual(
            self.defaults["whisper_image"], "ghcr.io/ggerganov/whisper.cpp:main"
        )
        self.assertEqual(self.defaults["whisper_model_name"], "base.en")
        self.assertIn("target_home", self.defaults["whisper_model_dir"])
        self.assertEqual(self.defaults["whisper_language"], "en")
        self.assertEqual(
            self.defaults["whisper_model_sha256"],
            "sha256:a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002",
        )

    def test_image_and_model_provisioning_are_idempotent(self):
        pull = next(task for task in self.tasks if task["name"] == "Pull whisper.cpp image")
        download = next(
            task for task in self.tasks if task["name"] == "Download and validate Whisper model"
        )
        self.assertEqual(
            pull["community.docker.docker_image_pull"]["name"], "{{ whisper_image }}"
        )
        self.assertNotIn("community.docker.docker_container", str(self.tasks))
        self.assertNotIn("published_ports", str(self.tasks))

        get_url = download["ansible.builtin.get_url"]
        self.assertEqual(get_url["checksum"], "{{ whisper_model_sha256 }}")
        self.assertEqual(get_url["url"], "{{ whisper_model_url }}")
        self.assertIn("{{ whisper_model_name }}", self.defaults["whisper_model_url"])
        self.assertIn("{{ whisper_model_name }}", get_url["dest"])
        self.assertNotIn("force", get_url)

    def test_install_tasks_use_idempotent_modules_and_user_ownership(self):
        directories = [
            task["ansible.builtin.file"]
            for task in self.tasks
            if "ansible.builtin.file" in task
        ]
        self.assertEqual(len(directories), 2)
        for directory in directories:
            self.assertEqual(directory["state"], "directory")
            self.assertEqual(directory["owner"], "{{ target_user }}")
            self.assertEqual(directory["group"], "{{ target_user }}")

        template = next(
            task["ansible.builtin.template"]
            for task in self.tasks
            if "ansible.builtin.template" in task
        )
        self.assertEqual(template["mode"], "0755")
        self.assertEqual(template["owner"], "{{ target_user }}")
        self.assertEqual(template["group"], "{{ target_user }}")
        for task in self.tasks:
            self.assertFalse(
                "ansible.builtin.shell" in task or "ansible.builtin.command" in task
            )


if __name__ == "__main__":
    unittest.main()
