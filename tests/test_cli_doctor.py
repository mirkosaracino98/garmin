from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import stat
import tempfile
import unittest

from tests.cli_helpers import run_cli, valid_setup_arguments



class DoctorCliTests(unittest.TestCase):
    def test_doctor_reports_uninitialized_store_without_creating_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = run_cli(temporary_directory, "doctor", "--format", "json")

            self.assertEqual(result.returncode, 3, result.stderr)
            response = json.loads(result.stdout)
            self.assertEqual(response["status"], "error")
            self.assertEqual(response["checks"][0]["name"], "store")
            self.assertEqual(response["checks"][0]["status"], "not_initialized")
            self.assertFalse((Path(temporary_directory) / "store.sqlite3").exists())

    def test_doctor_reports_valid_initialized_store(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            setup = run_cli(temporary_directory, *valid_setup_arguments())
            self.assertEqual(setup.returncode, 0, setup.stderr)

            result = run_cli(temporary_directory, "doctor", "--format", "json")

            self.assertEqual(result.returncode, 0, result.stderr)
            response = json.loads(result.stdout)
            self.assertEqual(response["status"], "ok")
            store_check = response["checks"][0]
            self.assertEqual(store_check["status"], "valid")
            self.assertEqual(store_check["schema_version"], "1.0")
            self.assertTrue(store_check["store_id"].startswith("store_"))

    def test_doctor_reports_incompatible_store(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            setup = run_cli(temporary_directory, *valid_setup_arguments())
            self.assertEqual(setup.returncode, 0, setup.stderr)
            database_path = Path(temporary_directory) / "store.sqlite3"
            connection = sqlite3.connect(database_path)
            try:
                connection.execute("PRAGMA user_version = 2")
            finally:
                connection.close()

            result = run_cli(temporary_directory, "doctor", "--format", "json")

            self.assertEqual(result.returncode, 5, result.stderr)
            response = json.loads(result.stdout)
            self.assertEqual(response["status"], "error")
            self.assertEqual(response["checks"][0]["status"], "incompatible")
            self.assertEqual(response["checks"][0]["found_schema_major"], 2)
            self.assertEqual(response["checks"][0]["supported_schema_major"], 1)

    def test_doctor_rejects_multiple_current_goals(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            setup = run_cli(temporary_directory, *valid_setup_arguments())
            self.assertEqual(setup.returncode, 0, setup.stderr)
            database_path = Path(temporary_directory) / "store.sqlite3"
            connection = sqlite3.connect(database_path)
            try:
                connection.execute("DROP INDEX one_current_configuration_revision")
                connection.execute(
                    """
                    INSERT INTO configuration_revisions(
                        kind, logical_id, revision_id, previous_revision_id, schema_version,
                        payload_json, content_hash, effective_from, recorded_at, run_id, is_current
                    )
                    SELECT kind, 'goal_other', 'rev_other', previous_revision_id, schema_version,
                           payload_json, content_hash, effective_from, recorded_at, run_id, 1
                    FROM configuration_revisions
                    WHERE kind = 'goal' AND is_current = 1
                    """
                )
                connection.commit()
            finally:
                connection.close()

            result = run_cli(temporary_directory, "doctor", "--format", "json")

            self.assertEqual(result.returncode, 5, result.stderr)
            self.assertEqual(json.loads(result.stdout)["checks"][0]["status"], "incompatible")

    def test_doctor_rejects_store_without_write_permission(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            setup = run_cli(temporary_directory, *valid_setup_arguments())
            self.assertEqual(setup.returncode, 0, setup.stderr)
            database_path = Path(temporary_directory) / "store.sqlite3"
            database_path.chmod(stat.S_IREAD)
            try:
                result = run_cli(temporary_directory, "doctor", "--format", "json")
            finally:
                database_path.chmod(stat.S_IREAD | stat.S_IWRITE)

            self.assertEqual(result.returncode, 5, result.stderr)
            response = json.loads(result.stdout)
            self.assertEqual(response["checks"][0]["status"], "incompatible")
            self.assertIn("permission", response["checks"][0]["message"])

if __name__ == "__main__":
    unittest.main()
