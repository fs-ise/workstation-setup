import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DockerWorkloadRoleTests(unittest.TestCase):
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
