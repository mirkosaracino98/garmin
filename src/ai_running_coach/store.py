from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from typing import Any
from uuid import uuid4

from ai_running_coach import __version__


APPLICATION_ID = 1_380_923_731
SCHEMA_MAJOR = 1
SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class RevisionResult:
    logical_id: str
    revision_id: str
    created: bool


class IncompatibleStoreError(RuntimeError):
    pass


class AthleteStore:
    def __init__(self, home: Path) -> None:
        self.home = home
        self.database_path = home / "store.sqlite3"

    def configure(
        self,
        configurations: dict[str, dict[str, Any]],
        run_id: str,
    ) -> dict[str, RevisionResult]:
        self.home.mkdir(parents=True, exist_ok=True)
        existed = self.database_path.exists()
        if existed:
            diagnosis = self.diagnose()
            if diagnosis["status"] != "valid":
                raise IncompatibleStoreError(str(diagnosis["message"]))
        with sqlite3.connect(self.database_path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            self._initialize(connection)
            effective_from = datetime.now(UTC).isoformat()
            results = {
                kind: self._record_revision(connection, kind, payload, run_id, effective_from)
                for kind, payload in configurations.items()
            }
            canonical_input = json.dumps(
                configurations, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            connection.execute(
                """
                INSERT INTO run_audits(
                    run_id, command, cli_version, input_hash, result_json, recorded_at
                ) VALUES (?, 'setup', ?, ?, ?, ?)
                """,
                (
                    run_id,
                    __version__,
                    hashlib.sha256(canonical_input.encode("utf-8")).hexdigest(),
                    json.dumps(
                        {
                            kind: {
                                "logical_id": result.logical_id,
                                "revision_id": result.revision_id,
                                "created": result.created,
                            }
                            for kind, result in results.items()
                        },
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    effective_from,
                ),
            )
        if os.name != "nt":
            self.home.chmod(0o700)
            self.database_path.chmod(0o600)
        return results

    def current_configurations(self) -> dict[str, dict[str, Any]]:
        if not self.database_path.exists():
            return {}
        diagnosis = self.diagnose()
        if diagnosis["status"] != "valid":
            raise IncompatibleStoreError(str(diagnosis["message"]))
        with sqlite3.connect(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT kind, payload_json
                FROM configuration_revisions
                WHERE is_current = 1
                """
            ).fetchall()
        return {kind: json.loads(payload_json) for kind, payload_json in rows}

    def diagnose(self) -> dict[str, Any]:
        if not self.database_path.exists():
            return {
                "name": "store",
                "status": "not_initialized",
                "message": "local store has not been initialized; run running-coach setup",
            }
        try:
            with sqlite3.connect(f"file:{self.database_path}?mode=ro", uri=True) as connection:
                return self._diagnose_connection(connection)
        except sqlite3.DatabaseError as error:
            return {
                "name": "store",
                "status": "incompatible",
                "message": f"local store is not a readable SQLite database: {error}",
                "supported_schema_major": SCHEMA_MAJOR,
            }

    def _diagnose_connection(self, connection: sqlite3.Connection) -> dict[str, Any]:
        application_id = int(connection.execute("PRAGMA application_id").fetchone()[0])
        schema_major = int(connection.execute("PRAGMA user_version").fetchone()[0])
        required_tables = {"metadata", "configuration_revisions", "run_audits"}
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        }
        if application_id != APPLICATION_ID or schema_major != SCHEMA_MAJOR or not required_tables <= tables:
            return {
                "name": "store",
                "status": "incompatible",
                "message": "local store schema is not supported by this version",
                "found_schema_major": schema_major,
                "supported_schema_major": SCHEMA_MAJOR,
            }
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            return {
                "name": "store",
                "status": "incompatible",
                "message": f"local store failed its integrity check: {integrity}",
                "found_schema_major": schema_major,
                "supported_schema_major": SCHEMA_MAJOR,
            }
        store_id_row = connection.execute(
            "SELECT value FROM metadata WHERE key = 'store_id'"
        ).fetchone()
        if store_id_row is None:
            return {
                "name": "store",
                "status": "incompatible",
                "message": "local store has no stable store identifier",
                "found_schema_major": schema_major,
                "supported_schema_major": SCHEMA_MAJOR,
            }
        current_rows = connection.execute(
            "SELECT kind, payload_json FROM configuration_revisions WHERE is_current = 1"
        ).fetchall()
        required_kinds = {"profile", "availability", "preferences", "goal"}
        if {row[0] for row in current_rows} != required_kinds:
            return {
                "name": "store",
                "status": "incompatible",
                "message": "local store has an incomplete configuration revision set",
                "found_schema_major": schema_major,
                "supported_schema_major": SCHEMA_MAJOR,
            }
        try:
            if not all(isinstance(json.loads(row[1]), dict) for row in current_rows):
                raise ValueError("configuration payload is not an object")
        except (json.JSONDecodeError, TypeError, ValueError) as error:
            return {
                "name": "store",
                "status": "incompatible",
                "message": f"local store has an invalid configuration payload: {error}",
                "found_schema_major": schema_major,
                "supported_schema_major": SCHEMA_MAJOR,
            }
        return {
            "name": "store",
            "status": "valid",
            "message": "local store is valid",
            "schema_version": SCHEMA_VERSION,
            "store_id": store_id_row[0],
        }

    def _initialize(self, connection: sqlite3.Connection) -> None:
        connection.executescript(
            f"""
            PRAGMA application_id = {APPLICATION_ID};
            PRAGMA user_version = {SCHEMA_MAJOR};
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS configuration_revisions (
                kind TEXT NOT NULL,
                logical_id TEXT NOT NULL,
                revision_id TEXT PRIMARY KEY,
                previous_revision_id TEXT,
                schema_version TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                effective_from TEXT NOT NULL,
                recorded_at TEXT NOT NULL,
                run_id TEXT NOT NULL,
                is_current INTEGER NOT NULL CHECK (is_current IN (0, 1)),
                FOREIGN KEY (previous_revision_id) REFERENCES configuration_revisions(revision_id)
            );
            CREATE TABLE IF NOT EXISTS run_audits (
                run_id TEXT PRIMARY KEY,
                command TEXT NOT NULL,
                cli_version TEXT NOT NULL,
                input_hash TEXT NOT NULL,
                result_json TEXT NOT NULL,
                recorded_at TEXT NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS one_current_configuration_revision
                ON configuration_revisions(kind, logical_id)
                WHERE is_current = 1;
            """
        )
        connection.execute(
            "INSERT OR IGNORE INTO metadata(key, value) VALUES ('store_id', ?)",
            (f"store_{uuid4().hex}",),
        )

    def _record_revision(
        self,
        connection: sqlite3.Connection,
        kind: str,
        payload: dict[str, Any],
        run_id: str,
        effective_from: str,
    ) -> RevisionResult:
        logical_id = {
            "profile": "profile_athlete",
            "availability": "availability_weekly",
            "preferences": "preferences_training",
            "goal": "goal_active_running",
        }[kind]
        canonical_payload = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        content_hash = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
        current = connection.execute(
            """
            SELECT revision_id, content_hash
            FROM configuration_revisions
            WHERE kind = ? AND logical_id = ? AND is_current = 1
            """,
            (kind, logical_id),
        ).fetchone()
        if current is not None and current[1] == content_hash:
            return RevisionResult(logical_id, current[0], False)

        revision_id = f"rev_{uuid4().hex}"
        previous_revision_id = current[0] if current is not None else None
        if previous_revision_id is not None:
            connection.execute(
                "UPDATE configuration_revisions SET is_current = 0 WHERE revision_id = ?",
                (previous_revision_id,),
            )
        connection.execute(
            """
            INSERT INTO configuration_revisions(
                kind, logical_id, revision_id, previous_revision_id, schema_version,
                payload_json, content_hash, effective_from, recorded_at, run_id, is_current
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                kind,
                logical_id,
                revision_id,
                previous_revision_id,
                SCHEMA_VERSION,
                canonical_payload,
                content_hash,
                effective_from,
                effective_from,
                run_id,
            ),
        )
        return RevisionResult(logical_id, revision_id, True)
