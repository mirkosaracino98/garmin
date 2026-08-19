from __future__ import annotations

import json
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from tests.cli_helpers import run_cli, valid_setup_arguments


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from ai_running_coach.cli import main  # noqa: E402


class TtyBuffer(io.StringIO):
    def isatty(self) -> bool:
        return True


class SetupCliTests(unittest.TestCase):
    def test_athlete_can_initialize_store_non_interactively(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = run_cli(
                temporary_directory,
                "setup",
                "--non-interactive",
                "--name",
                "Ada",
                "--available-days",
                "tuesday,thursday,sunday",
                "--preferred-long-run-day",
                "sunday",
                "--goal-type",
                "10k",
                "--goal-date",
                "2027-04-11",
                "--goal-mode",
                "time",
                "--target-time",
                "00:49:30",
                "--goal-priority",
                "high",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            response = json.loads(result.stdout)
            self.assertEqual(response["status"], "configured")
            self.assertEqual(response["schema_version"], "1.0")
            self.assertEqual(response["profile"]["name"], "Ada")
            self.assertEqual(
                response["availability"]["available_days"],
                ["tuesday", "thursday", "sunday"],
            )
            self.assertEqual(response["preferences"]["planned_gym_days"], ["monday", "friday"])
            self.assertEqual(response["goal"]["type"], "10k")
            self.assertEqual(response["goal"]["target_time_seconds"], 2970)
            self.assertTrue(response["profile_id"].startswith("profile_"))
            self.assertTrue(response["goal_id"].startswith("goal_"))
            self.assertTrue((Path(temporary_directory) / "store.sqlite3").is_file())

    def test_replay_is_idempotent_and_correction_revises_only_changed_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            original = run_cli(temporary_directory, *valid_setup_arguments())
            replay = run_cli(temporary_directory, *valid_setup_arguments())
            correction = run_cli(
                temporary_directory,
                "setup",
                "--non-interactive",
                "--goal-priority",
                "medium",
            )

            self.assertEqual(original.returncode, 0, original.stderr)
            self.assertEqual(replay.returncode, 0, replay.stderr)
            self.assertEqual(correction.returncode, 0, correction.stderr)
            original_response = json.loads(original.stdout)
            replay_response = json.loads(replay.stdout)
            correction_response = json.loads(correction.stdout)

            self.assertEqual(replay_response["profile_id"], original_response["profile_id"])
            self.assertEqual(replay_response["goal_id"], original_response["goal_id"])
            self.assertTrue(all(not revision["created"] for revision in replay_response["revisions"].values()))
            for kind in ("profile", "availability", "preferences"):
                self.assertEqual(
                    correction_response["revisions"][kind]["revision_id"],
                    original_response["revisions"][kind]["revision_id"],
                )
                self.assertFalse(correction_response["revisions"][kind]["created"])
            self.assertNotEqual(
                correction_response["revisions"]["goal"]["revision_id"],
                original_response["revisions"]["goal"]["revision_id"],
            )
            self.assertTrue(correction_response["revisions"]["goal"]["created"])
            self.assertEqual(correction_response["profile"], original_response["profile"])
            self.assertEqual(correction_response["goal"]["priority"], "medium")

    def test_all_supported_goal_types_accept_completion_or_target_time(self) -> None:
        cases = (
            ("general", "completion", None),
            ("5k", "time", "00:24:00"),
            ("10k", "time", "00:50:00"),
            ("half-marathon", "completion", None),
            ("marathon", "time", "04:15:00"),
        )
        for goal_type, goal_mode, target_time in cases:
            with self.subTest(goal_type=goal_type), tempfile.TemporaryDirectory() as temporary_directory:
                arguments = [
                    "setup",
                    "--non-interactive",
                    "--name",
                    "Ada",
                    "--available-days",
                    "tuesday,thursday,sunday",
                    "--preferred-long-run-day",
                    "sunday",
                    "--goal-type",
                    goal_type,
                    "--goal-date",
                    "2027-04-11",
                    "--goal-mode",
                    goal_mode,
                    "--goal-priority",
                    "high",
                ]
                if target_time is not None:
                    arguments.extend(("--target-time", target_time))

                result = run_cli(temporary_directory, *arguments)

                self.assertEqual(result.returncode, 0, result.stderr)
                response = json.loads(result.stdout)
                self.assertEqual(response["goal"]["type"], goal_type)
                self.assertEqual(response["goal"]["mode"], goal_mode)

    def test_non_tty_requires_explicit_non_interactive_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            arguments = valid_setup_arguments()
            arguments.remove("--non-interactive")

            result = run_cli(temporary_directory, *arguments)

            self.assertEqual(result.returncode, 2)
            self.assertEqual(
                json.loads(result.stdout)["error"]["code"],
                "TTY_REQUIRED",
            )
            self.assertEqual(result.stderr, "")

    def test_invalid_non_interactive_input_returns_structured_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = run_cli(
                temporary_directory,
                "setup",
                "--non-interactive",
                "--goal-type",
                "ultramarathon",
            )

            self.assertEqual(result.returncode, 2)
            response = json.loads(result.stdout)
            self.assertEqual(response["status"], "error")
            self.assertEqual(response["error"]["code"], "INVALID_INPUT")
            self.assertNotEqual(response["error"]["message"], "")
            self.assertEqual(result.stderr, "")

    def test_prompted_goal_values_are_validated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = TtyBuffer()
            prompted_values = [
                "Ada",
                "Europe/Rome",
                "tuesday,thursday,sunday",
                "sunday",
                "ultramarathon",
                "2027-04-11",
                "completion",
                "high",
            ]
            with (
                patch.dict(os.environ, {"RUNNING_COACH_HOME": temporary_directory}),
                patch("sys.stdin", TtyBuffer()),
                patch("sys.stdout", output),
                patch("builtins.input", side_effect=prompted_values),
            ):
                exit_code = main(["setup", "--format", "json"])

            self.assertEqual(exit_code, 2)
            self.assertEqual(json.loads(output.getvalue())["error"]["code"], "INVALID_INPUT")
            self.assertFalse((Path(temporary_directory) / "store.sqlite3").exists())

if __name__ == "__main__":
    unittest.main()
