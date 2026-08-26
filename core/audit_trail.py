import getpass
import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class ImmutableAuditLog:
    """Unveränderliches Audit-Log-System basierend auf kryptographischer Hash-Kettung (Kryptographische Verkettung / Blockchain-Prinzip).

    Garantiert die Revisionssicherheit gemäß GoBD und ISO 27001 für geodätische und ziviltechnische Berechnungen.
    """

    GENESIS_HASH: str = "0000000000000000000000000000000000000000000000000000000000000000"

    def __init__(self, db_path: str | Path = "audit_log.db") -> None:
        """Initialisiert die Audit-Datenbank verbindungssicher und erstellt das Schema."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Erstellt eine neue SQLite-Verbindung mit optimierter Performance und Thread-Sicherheit."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_database(self) -> None:
        """Erzeugt das Schema für die fälschungssichere Protokollierung, falls nicht vorhanden."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_trail (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    action TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    current_hash TEXT NOT NULL UNIQUE
                );
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp 
                ON audit_trail(timestamp);
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_audit_hash 
                ON audit_trail(current_hash);
                """
            )
            conn.commit()

    def _compute_hash(
        self,
        timestamp: str,
        action: str,
        user_id: str,
        details_json: str,
        previous_hash: str,
    ) -> str:
        """Berechnet den SHA-256 Hashwert über alle Datensatzkomponenten inklusive Vorgänger-Hash."""
        hasher = hashlib.sha256()
        payload = f"{timestamp}|{action}|{user_id}|{details_json}|{previous_hash}"
        hasher.update(payload.encode("utf-8"))
        return hasher.hexdigest()

    def get_last_hash(self) -> str:
        """Ermittelt den SHA-256 Hash des zuletzt geschriebenen Audit-Eintrags."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT current_hash FROM audit_trail ORDER BY id DESC LIMIT 1;"
            )
            row = cursor.fetchone()
            if row:
                return str(row["current_hash"])
            return self.GENESIS_HASH

    def log_action(
        self,
        action: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Registriert eine neue Transaktion im Audit-Log mit strikter Hash-Verkettung.

        Args:
            action: Beschreibung der ausgeführten Systemaktion.
            user_id: Benutzerkennung (standardmäßig aktueller Betriebssystemnutzer).
            details: Zusätzliche strukturierte Metadaten zur Transaktion.

        Returns:
            Der berechnete SHA-256 Hash des erzeugten Eintrags.
        """
        if user_id is None:
            user_id = getpass.getuser()

        if details is None:
            details = {}

        timestamp = datetime.now(timezone.utc).isoformat()
        details_json = json.dumps(details, sort_keys=True, ensure_ascii=False)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("BEGIN EXCLUSIVE TRANSACTION;")

            cursor.execute(
                "SELECT current_hash FROM audit_trail ORDER BY id DESC LIMIT 1;"
            )
            row = cursor.fetchone()
            previous_hash = row["current_hash"] if row else self.GENESIS_HASH

            current_hash = self._compute_hash(
                timestamp=timestamp,
                action=action,
                user_id=user_id,
                details_json=details_json,
                previous_hash=previous_hash,
            )

            cursor.execute(
                """
                INSERT INTO audit_trail 
                (timestamp, action, user_id, details_json, previous_hash, current_hash)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    timestamp,
                    action,
                    user_id,
                    details_json,
                    previous_hash,
                    current_hash,
                ),
            )
            conn.commit()

        return current_hash

    def verify_chain(self) -> Tuple[bool, int, str]:
        """Prüft die gesamte Datenbank auf Manipulationen durch lückenlose Neuberechnung aller Hashes."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, timestamp, action, user_id, details_json, previous_hash, current_hash 
                FROM audit_trail ORDER BY id ASC;
                """
            )
            rows = cursor.fetchall()

            if not rows:
                return True, 0, "Protokoll ist leer und somit intakt."

            expected_previous_hash = self.GENESIS_HASH

            for row in rows:
                entry_id = row["id"]
                timestamp = row["timestamp"]
                action = row["action"]
                user_id = row["user_id"]
                details_json = row["details_json"]
                previous_hash = row["previous_hash"]
                current_hash = row["current_hash"]

                if previous_hash != expected_previous_hash:
                    return (
                        False,
                        entry_id,
                        f"Verkettungsfehler bei ID {entry_id}: Vorgänger-Hash stimmt nicht überein.",
                    )

                recalculated_hash = self._compute_hash(
                    timestamp=timestamp,
                    action=action,
                    user_id=user_id,
                    details_json=details_json,
                    previous_hash=previous_hash,
                )

                if recalculated_hash != current_hash:
                    return (
                        False,
                        entry_id,
                        f"Integritätsverletzung bei ID {entry_id}: Hashwert ungültig.",
                    )

                expected_previous_hash = current_hash

        return True, 0, "Die Integrität der Audit-Kette wurde erfolgreich verifiziert."

    def fetch_logs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, timestamp, action, user_id, details_json, previous_hash, current_hash
                FROM audit_trail
                ORDER BY id DESC
                LIMIT ? OFFSET ?;
                """,
                (limit, offset),
            )
            rows = cursor.fetchall()

            results = []
            for r in rows:
                results.append(
                    {
                        "id": r["id"],
                        "timestamp": r["timestamp"],
                        "action": r["action"],
                        "user_id": r["user_id"],
                        "details": json.loads(r["details_json"]),
                        "previous_hash": r["previous_hash"],
                        "current_hash": r["current_hash"],
                    }
                )
            return results