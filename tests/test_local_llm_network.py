"""Regression checks for the local LLM Docker network migration."""

from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path):
    with path.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


class LocalLlmNetworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.defaults = load_yaml(ROOT / "roles/local_llm/defaults/main.yml")
        cls.tasks = load_yaml(ROOT / "roles/local_llm/tasks/main.yml")

    def test_network_subnet_has_safe_configurable_default(self):
        self.assertEqual(self.defaults["local_llm_network_subnet"], "10.240.0.0/24")
        self.assertNotEqual(self.defaults["local_llm_network_subnet"], "172.18.0.0/16")

        network_task = next(
            task
            for task in self.tasks
            if task["name"] == "Ensure dedicated Docker network exists with configured subnet"
        )
        self.assertEqual(
            network_task["community.docker.docker_network"]["ipam_config"],
            [{"subnet": "{{ local_llm_network_subnet }}"}],
        )

    def test_wrong_network_is_replaced_after_services_stop(self):
        names = [task["name"] for task in self.tasks]
        inspect_at = names.index("Inspect dedicated Docker network")
        stop_webui_at = names.index("Stop Open WebUI before replacing its network")
        stop_ollama_at = names.index("Stop Ollama before replacing its network")
        remove_at = names.index("Remove existing Docker network with incorrect subnet")
        create_at = names.index("Ensure dedicated Docker network exists with configured subnet")
        start_ollama_at = names.index("Run Ollama container")
        start_webui_at = names.index("Run Open WebUI container")

        self.assertLess(inspect_at, stop_webui_at)
        self.assertLess(stop_webui_at, stop_ollama_at)
        self.assertLess(stop_ollama_at, remove_at)
        self.assertLess(remove_at, create_at)
        self.assertLess(create_at, start_ollama_at)
        self.assertLess(start_ollama_at, start_webui_at)

        removal = self.tasks[remove_at]["community.docker.docker_network"]
        self.assertEqual(removal["state"], "absent")
        self.assertTrue(removal["force"])
        for task_at in (stop_webui_at, stop_ollama_at, remove_at):
            self.assertEqual(
                self.tasks[task_at]["when"],
                [
                    "local_llm_network_info.exists",
                    "local_llm_network_subnets != [local_llm_network_subnet]",
                ],
            )

    def test_containers_reconnect_and_keep_persistent_bind_mounts(self):
        for task_name, expected_volume in (
            ("Run Ollama container", "{{ local_llm_ollama_models_dir }}:/root/.ollama"),
            ("Run Open WebUI container", "{{ local_llm_webui_data_dir }}:/app/backend/data"),
        ):
            task = next(task for task in self.tasks if task["name"] == task_name)
            container = task["community.docker.docker_container"]
            self.assertEqual(container["state"], "started")
            self.assertEqual(container["networks"], [{"name": "{{ local_llm_network_name }}"}])
            self.assertIn(expected_volume, container["volumes"])


if __name__ == "__main__":
    unittest.main()
