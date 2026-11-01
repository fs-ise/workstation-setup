import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import yaml
from jinja2 import Environment, StrictUndefined


ROOT = Path(__file__).resolve().parents[1]


class WhisperCliTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.model_directory = self.root / "persistent models"
        self.model_directory.mkdir()
        (self.model_directory / "ggml-base.en.bin").write_bytes(b"mock model")

        defaults = yaml.safe_load(
            (ROOT / "roles/whisper/defaults/main.yml").read_text(encoding="utf-8")
        )
        template = (ROOT / "roles/whisper/templates/transcribe.py.j2").read_text(
            encoding="utf-8"
        )
        environment = Environment(undefined=StrictUndefined)
        environment.filters["to_json"] = json.dumps
        rendered = environment.from_string(template).render(
            whisper_image=defaults["whisper_image"],
            whisper_model_name=defaults["whisper_model_name"],
            whisper_language=defaults["whisper_language"],
            whisper_model_dir=str(self.model_directory),
        )
        script = self.root / "transcribe.py"
        script.write_text(rendered, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("whisper_transcribe_test", script)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def run_cli(self, arguments):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            status = self.module.main(arguments)
        return status, stdout.getvalue(), stderr.getvalue()

    def mock_successful_container(self, command, check=False):
        volume_index = command.index("--volume")
        work_mount = command[volume_index + 1]
        work_directory = Path(work_mount.removesuffix(":/work:Z"))
        self.assertEqual((work_directory / "input.media").read_bytes(), b"audio or video")
        (work_directory / "transcription.txt").write_text(
            "recognized words\n", encoding="utf-8"
        )
        return SimpleNamespace(returncode=0)

    def make_input(self, directory, name="recording.mp4"):
        directory.mkdir(parents=True, exist_ok=True)
        input_file = directory / name
        input_file.write_bytes(b"audio or video")
        input_file.chmod(0o640)
        return input_file

    def test_parser_accepts_model_and_language_after_input(self):
        arguments = self.module.build_parser().parse_args(
            ["recording.mp4", "--model", "base.en", "--language", "en"]
        )
        self.assertEqual(arguments.input, "recording.mp4")
        self.assertEqual(arguments.model, "base.en")
        self.assertEqual(arguments.language, "en")
        self.assertFalse(arguments.overwrite)

    def test_help_is_available_without_running_docker(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout), self.assertRaises(SystemExit) as result:
            self.module.main(["--help"])
        self.assertEqual(result.exception.code, 0)
        self.assertIn("--overwrite", stdout.getvalue())
        self.assertIn("--language", stdout.getvalue())

    def test_output_filename_uses_input_stem_and_preserves_spaces(self):
        input_path = Path("/projects/Project recordings/meeting.final.mp4")
        self.assertEqual(
            self.module.output_path_for(input_path),
            Path("/projects/Project recordings/meeting.final.txt"),
        )

    def test_paths_with_spaces_work_and_mounts_are_selinux_aware(self):
        directory = self.root / "Project recordings"
        input_file = self.make_input(directory, "committee meeting.mp4")
        original_mode = input_file.stat().st_mode & 0o777
        recorded_command = []

        def run_container(command, check=False):
            recorded_command.extend(command)
            return self.mock_successful_container(command, check)

        with patch.object(self.module.subprocess, "run", side_effect=run_container):
            status, stdout, stderr = self.run_cli([str(input_file)])

        output = directory / "committee meeting.txt"
        self.assertEqual(status, 0, stderr)
        self.assertTrue(output.is_file())
        self.assertEqual(output.read_text(encoding="utf-8"), "recognized words\n")
        self.assertEqual(output.stat().st_uid, os.getuid())
        self.assertEqual(input_file.stat().st_mode & 0o777, original_mode)
        self.assertIn(str(output), stdout)
        self.assertIn("--rm", recorded_command)
        mounts = [
            recorded_command[index + 1]
            for index, value in enumerate(recorded_command[:-1])
            if value == "--volume"
        ]
        self.assertTrue(any(mount.endswith(":/work:Z") for mount in mounts))
        self.assertTrue(
            any(mount.endswith(":/models:ro,Z") for mount in mounts), mounts
        )
        self.assertIn("/app/build/bin/whisper-cli", recorded_command[-1])
        self.assertIn("-ac 1 -ar 16000 -c:a pcm_s16le", recorded_command[-1])

    def test_relative_input_works_from_an_unrelated_working_directory(self):
        working_directory = self.root / "unrelated project directory"
        input_file = self.make_input(working_directory, "relative recording.wav")
        original_directory = Path.cwd()
        try:
            os.chdir(working_directory)
            with patch.object(
                self.module.subprocess,
                "run",
                side_effect=self.mock_successful_container,
            ):
                status, _, stderr = self.run_cli(["relative recording.wav"])
        finally:
            os.chdir(original_directory)

        self.assertEqual(status, 0, stderr)
        self.assertEqual(
            (working_directory / "relative recording.txt").read_text(encoding="utf-8"),
            "recognized words\n",
        )

    def test_missing_input_has_a_useful_error_and_does_not_run_docker(self):
        with patch.object(self.module.subprocess, "run") as run_container:
            status, _, stderr = self.run_cli([str(self.root / "missing.mp4")])
        self.assertEqual(status, 1)
        self.assertIn("input file does not exist", stderr)
        run_container.assert_not_called()

    def test_missing_model_has_a_useful_error_and_does_not_run_docker(self):
        input_file = self.make_input(self.root, "missing-model.wav")
        with patch.object(self.module.subprocess, "run") as run_container:
            status, _, stderr = self.run_cli([str(input_file), "--model", "small.en"])
        self.assertEqual(status, 1)
        self.assertIn("model 'small.en' is not installed", stderr)
        run_container.assert_not_called()

    def test_existing_output_is_preserved_unless_overwrite_is_explicit(self):
        input_file = self.make_input(self.root, "lecture.wav")
        output = self.root / "lecture.txt"
        output.write_text("keep this transcription\n", encoding="utf-8")

        with patch.object(self.module.subprocess, "run") as run_container:
            status, _, stderr = self.run_cli([str(input_file)])
        self.assertEqual(status, 1)
        self.assertIn("use --overwrite", stderr)
        self.assertEqual(output.read_text(encoding="utf-8"), "keep this transcription\n")
        run_container.assert_not_called()

        with patch.object(
            self.module.subprocess, "run", side_effect=self.mock_successful_container
        ):
            status, _, stderr = self.run_cli([str(input_file), "--overwrite"])
        self.assertEqual(status, 0, stderr)
        self.assertEqual(output.read_text(encoding="utf-8"), "recognized words\n")
        self.assertEqual(output.stat().st_uid, os.getuid())

    def test_conversion_failure_reports_error_and_cleans_temporary_files(self):
        input_file = self.make_input(self.root, "broken.mp4")
        temporary_paths = []

        def failed_conversion(command, check=False):
            work_mount = command[command.index("--volume") + 1]
            temporary_paths.append(Path(work_mount.removesuffix(":/work:Z")))
            return SimpleNamespace(returncode=73)

        with patch.object(self.module.subprocess, "run", side_effect=failed_conversion):
            status, _, stderr = self.run_cli([str(input_file)])
        self.assertEqual(status, 1)
        self.assertIn("FFmpeg could not convert", stderr)
        self.assertTrue(temporary_paths)
        self.assertFalse(temporary_paths[0].exists())
        self.assertFalse((self.root / "broken.txt").exists())

    def test_docker_start_failure_is_reported(self):
        input_file = self.make_input(self.root, "docker-error.mp3")
        with patch.object(
            self.module.subprocess,
            "run",
            return_value=SimpleNamespace(returncode=125),
        ):
            status, _, stderr = self.run_cli([str(input_file)])
        self.assertEqual(status, 1)
        self.assertIn("Docker could not start", stderr)


if __name__ == "__main__":
    unittest.main()
