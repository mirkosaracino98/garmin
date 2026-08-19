from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class DoctorCliTests(unittest.TestCase):
    def test_doctor_reports_uninitialized_store_without_creating_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = self.run_cli(temporary_directory, "doctor", "--format", "json")

            self.assertEqual(result.returncode, 3, result.stderr)
            response = json.loads(result.stdout)
            self.assertEqual(response["status"], "error")
            self.assertEqual(response["checks"][0]["name"], "store")
            self.assertEqual(response["checks"][0]["status"], "not_initialized")
            self.assertFalse((Path(temporary_directory) / "store.sqlite3").exists())

    def test_doctor_reports_valid_initialized_store(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            setup = self.run_cli(temporary_directory, *self.valid_setup_arguments())
            self.assertEqual(setup.returncode, 0, setup.stderr)

            result = self.run_cli(temporary_directory, "doctor", "--format", "json")

            self.assertEqual(result.returncode, 0, result.stderr)
            response = json.loads(result.stdout)
            self.assertEqual(response["status"], "ok")
            store_check = response["checks"][0]
            self.assertEqual(store_check["status"], "valid")
            self.assertEqual(store_check["schema_version"], "1.0")
            self.assertTrue(store_check["store_id"].startswith("store_"))

    def test_doctor_reports_incompatible_store(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            setup = self.run_cli(temporary_directory, *self.valid_setup_arguments())
            self.assertEqual(setup.returncode, 0, setup.stderr)
            database_path = Path(temporary_directory) / "store.sqlite3"
            connection = sqlite3.connect(database_path)
            try:
                connection.execute("PRAGMA user_version = 2")
            finally:
                connection.close()

            result = self.run_cli(temporary_directory, "doctor", "--format", "json")

            self.assertEqual(result.returncode, 5, result.stderr)
            response = json.loads(result.stdout)
            self.assertEqual(response["status"], "error")
            self.assertEqual(response["checks"][0]["status"], "incompatible")
            self.assertEqual(response["checks"][0]["found_schema_major"], 2)
            self.assertEqual(response["checks"][0]["supported_schema_major"], 1)

    def run_cli(self, home: str, *arguments: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["RUNNING_COACH_HOME"] = home
        environment["PYTHONPATH"] = str(REPOSITORY_ROOT / "src")
        return subprocess.run(
            [sys.executable, "-m", "ai_running_coach", *arguments],
            cwd=REPOSITORY_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def valid_setup_arguments(self) -> list[str]:
        return [
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
            "completion",
            "--goal-priority",
            "high",
        ]


if __name__ == "__main__":
    unittest.main()
