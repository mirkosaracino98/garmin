from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def run_cli(home: str, *arguments: str) -> subprocess.CompletedProcess[str]:
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


def valid_setup_arguments() -> list[str]:
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
