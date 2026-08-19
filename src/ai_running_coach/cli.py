from __future__ import annotations

import argparse
from datetime import date
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, NoReturn, Sequence
from uuid import uuid4

from ai_running_coach import __version__
from ai_running_coach.store import AthleteStore, IncompatibleStoreError, SCHEMA_VERSION


DAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
GOAL_TYPES = ("general", "5k", "10k", "half-marathon", "marathon")


class CliInputError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise CliInputError("INVALID_INPUT", message)


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(prog="running-coach")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    setup = subparsers.add_parser("setup", help="Configure the local athlete store")
    setup.add_argument("--non-interactive", action="store_true")
    setup.add_argument("--format", choices=("human", "json"), default=None)
    setup.add_argument("--name")
    setup.add_argument("--timezone")
    setup.add_argument("--available-days")
    setup.add_argument("--preferred-long-run-day", choices=DAYS)
    setup.add_argument("--goal-type", choices=GOAL_TYPES)
    setup.add_argument("--goal-date")
    setup.add_argument("--goal-mode", choices=("completion", "time"))
    setup.add_argument("--target-time")
    setup.add_argument("--goal-priority", choices=("low", "medium", "high"))
    doctor = subparsers.add_parser("doctor", help="Diagnose the local athlete store")
    doctor.add_argument("--format", choices=("human", "json"), default="human")
    doctor.add_argument("--non-interactive", action="store_true")
    return parser


def _parse_days(value: str) -> list[str]:
    days = list(dict.fromkeys(day.strip().lower() for day in value.split(",") if day.strip()))
    invalid = [day for day in days if day not in DAYS]
    if not days or invalid:
        raise ValueError("available days must be a comma-separated list of weekday names")
    return days


def _parse_target_time(value: str | None, mode: str) -> int | None:
    if mode == "completion":
        if value is not None:
            raise ValueError("target time is not allowed when goal mode is completion")
        return None
    if value is None:
        raise ValueError("target time is required when goal mode is time")
    match = re.fullmatch(r"(\d{1,2}):(\d{2}):(\d{2})", value)
    if match is None:
        raise ValueError("target time must use HH:MM:SS")
    hours, minutes, seconds = (int(part) for part in match.groups())
    if minutes > 59 or seconds > 59 or hours == 0 and minutes == 0 and seconds == 0:
        raise ValueError("target time must be a positive HH:MM:SS duration")
    return hours * 3600 + minutes * 60 + seconds


def _home() -> Path:
    configured = os.environ.get("RUNNING_COACH_HOME")
    if configured:
        return Path(configured)
    if os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "running-coach"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "running-coach"
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    return (
        Path(xdg_data_home) / "running-coach"
        if xdg_data_home
        else Path.home() / ".local" / "share" / "running-coach"
    )


def _prompt(label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    response = input(f"{label}{suffix}: ").strip()
    return response or default or ""


def _format_duration(seconds: int | None) -> str | None:
    if seconds is None:
        return None
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _collect_interactive_input(
    arguments: argparse.Namespace,
    current: dict[str, dict[str, object]],
) -> None:
    profile = current.get("profile", {})
    availability = current.get("availability", {})
    preferences = current.get("preferences", {})
    goal = current.get("goal", {})
    arguments.name = arguments.name or _prompt("Name", str(profile.get("name", "")) or None)
    arguments.timezone = arguments.timezone or _prompt(
        "Timezone", str(profile.get("timezone", "Europe/Rome"))
    )
    current_days = availability.get("available_days", [])
    days_default = (
        ",".join(str(day) for day in current_days) or None
        if isinstance(current_days, list)
        else None
    )
    arguments.available_days = arguments.available_days or _prompt("Available days", days_default)
    arguments.preferred_long_run_day = arguments.preferred_long_run_day or _prompt(
        "Preferred long-run day",
        str(preferences.get("preferred_long_run_day", "")) or None,
    )
    arguments.goal_type = arguments.goal_type or _prompt(
        "Goal type", str(goal.get("type", "")) or None
    )
    arguments.goal_date = arguments.goal_date or _prompt(
        "Goal date (YYYY-MM-DD)", str(goal.get("date", "")) or None
    )
    arguments.goal_mode = arguments.goal_mode or _prompt(
        "Goal mode (completion/time)", str(goal.get("mode", "")) or None
    )
    if arguments.goal_mode == "time" and arguments.target_time is None:
        stored_target = goal.get("target_time_seconds")
        default_target = _format_duration(stored_target if isinstance(stored_target, int) else None)
        arguments.target_time = _prompt("Target time (HH:MM:SS)", default_target)
    arguments.goal_priority = arguments.goal_priority or _prompt(
        "Goal priority (low/medium/high)", str(goal.get("priority", "")) or None
    )


def run_setup(arguments: argparse.Namespace) -> dict[str, Any]:
    store = AthleteStore(_home())
    current = store.current_configurations()
    if not arguments.non_interactive:
        _collect_interactive_input(arguments, current)
    profile = {**current.get("profile", {})}
    availability = {**current.get("availability", {})}
    preferences = {**current.get("preferences", {})}
    goal = {**current.get("goal", {})}

    if arguments.name is not None:
        profile["name"] = arguments.name.strip()
    if arguments.timezone is not None:
        profile["timezone"] = arguments.timezone
    profile.setdefault("timezone", "Europe/Rome")
    if arguments.available_days is not None:
        availability["available_days"] = _parse_days(arguments.available_days)
    if arguments.preferred_long_run_day is not None:
        preferences["preferred_long_run_day"] = arguments.preferred_long_run_day
    preferences.setdefault("planned_gym_days", ["monday", "friday"])
    preferences.setdefault("unit_system", "metric")
    if arguments.goal_type is not None:
        goal["type"] = arguments.goal_type
    if arguments.goal_date is not None:
        goal["date"] = date.fromisoformat(arguments.goal_date).isoformat()
    if arguments.goal_mode is not None:
        goal["mode"] = arguments.goal_mode
    if arguments.goal_priority is not None:
        goal["priority"] = arguments.goal_priority
    if arguments.target_time is not None:
        goal["target_time_seconds"] = _parse_target_time(arguments.target_time, goal.get("mode", ""))
    elif arguments.goal_mode == "completion":
        goal["target_time_seconds"] = None

    missing = [
        label
        for label, present in (
            ("name", bool(profile.get("name"))),
            ("available days", bool(availability.get("available_days"))),
            ("preferred long-run day", bool(preferences.get("preferred_long_run_day"))),
            ("goal type", bool(goal.get("type"))),
            ("goal date", bool(goal.get("date"))),
            ("goal mode", bool(goal.get("mode"))),
            ("goal priority", bool(goal.get("priority"))),
        )
        if not present
    ]
    if missing:
        raise ValueError(f"missing setup input: {', '.join(missing)}")
    if goal["type"] not in GOAL_TYPES:
        raise ValueError(f"goal type must be one of: {', '.join(GOAL_TYPES)}")
    if goal["mode"] not in ("completion", "time"):
        raise ValueError("goal mode must be completion or time")
    if goal["priority"] not in ("low", "medium", "high"):
        raise ValueError("goal priority must be low, medium, or high")
    available_days = availability["available_days"]
    if preferences["preferred_long_run_day"] not in available_days:
        raise ValueError("preferred long-run day must be one of the available days")
    if goal["mode"] == "time" and goal.get("target_time_seconds") is None:
        raise ValueError("target time is required when goal mode is time")
    if goal["mode"] == "completion":
        goal["target_time_seconds"] = None
    configurations = {
        "profile": profile,
        "availability": availability,
        "preferences": preferences,
        "goal": goal,
    }
    run_id = f"run_{uuid4().hex}"
    revisions = store.configure(configurations, run_id)
    return {
        "status": "configured",
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "profile_id": revisions["profile"].logical_id,
        "goal_id": revisions["goal"].logical_id,
        **configurations,
        "revisions": {
            kind: {"revision_id": result.revision_id, "created": result.created}
            for kind, result in revisions.items()
        },
    }


def run_doctor() -> tuple[dict[str, Any], int]:
    check = AthleteStore(_home()).diagnose()
    exit_code = {"valid": 0, "not_initialized": 3, "incompatible": 5}[str(check["status"])]
    return {"status": "ok" if exit_code == 0 else "error", "checks": [check]}, exit_code


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        arguments = parser.parse_args(argv)
        if arguments.command == "doctor":
            result, exit_code = run_doctor()
            if arguments.format == "json":
                print(json.dumps(result, ensure_ascii=False, sort_keys=True))
            else:
                check = result["checks"][0]
                print(f"store: {check['status']} - {check['message']}")
            return exit_code
        if not arguments.non_interactive and not (sys.stdin.isatty() and sys.stdout.isatty()):
            raise CliInputError(
                "TTY_REQUIRED",
                "interactive mode requires a TTY; use --non-interactive with explicit input",
            )
        result = run_setup(arguments)
    except IncompatibleStoreError as error:
        print(
            json.dumps(
                {"status": "error", "error": {"code": "INCOMPATIBLE_STORE", "message": str(error)}}
            )
        )
        return 5
    except (ValueError, CliInputError) as error:
        code = error.code if isinstance(error, CliInputError) else "INVALID_INPUT"
        print(json.dumps({"status": "error", "error": {"code": code, "message": str(error)}}))
        return 2
    if arguments.non_interactive or arguments.format == "json":
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(
            f"Configured {result['profile_id']} with active goal {result['goal_id']} "
            f"({result['goal']['type']}, {result['goal']['date']})."
        )
    return 0
