from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_wheel_installs_with_single_running_coach_entry_point(self) -> None:
        with (REPOSITORY_ROOT / "pyproject.toml").open("rb") as configuration_file:
            configuration = tomllib.load(configuration_file)
        self.assertEqual(
            configuration["project"]["scripts"],
            {"running-coach": "ai_running_coach.cli:main"},
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            distribution_directory = temporary_path / "dist"
            build = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "build",
                    "--wheel",
                    "--no-isolation",
                    "--outdir",
                    str(distribution_directory),
                ],
                cwd=REPOSITORY_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(build.returncode, 0, build.stderr)
            wheel = next(distribution_directory.glob("*.whl"))
            environment_directory = temporary_path / "isolated"
            create_environment = subprocess.run(
                [sys.executable, "-m", "venv", str(environment_directory)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(create_environment.returncode, 0, create_environment.stderr)
            environment_python = environment_directory / "Scripts" / "python.exe"
            install = subprocess.run(
                [str(environment_python), "-m", "pip", "install", "--no-deps", str(wheel)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(install.returncode, 0, install.stderr)

            executable = environment_directory / "Scripts" / "running-coach.exe"
            help_result = subprocess.run(
                [str(executable), "--help"],
                env={**os.environ, "RUNNING_COACH_HOME": str(temporary_path / "home")},
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(help_result.returncode, 0, help_result.stderr)
            self.assertIn("{setup,doctor}", help_result.stdout)


if __name__ == "__main__":
    unittest.main()
