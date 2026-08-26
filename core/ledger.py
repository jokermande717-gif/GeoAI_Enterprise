import os
import sqlite3
import hashlib
import json
from datetime import datetime

class GeodeticBlockchainLedger:
    def __init__(self, db_name="geoai_audit_chain.db"):
        # استخدام مجلد AppData لضمان وجود صلاحيات الكتابة دائمًا
        app_data_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "GeoAI_Enterprise")
        os.makedirs(app_data_dir, exist_ok=True)
        self.db_path = os.path.join(app_data_dir, db_name)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_blocks (
                    block_index INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    action TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    prev_hash TEXT NOT NULL,
                    block_hash TEXT NOT NULL
                )
            """)
            conn.commit()
            
            cursor.execute("SELECT COUNT(*) FROM audit_blocks")
            if cursor.fetchone()[0] == 0:
                self._create_genesis_block(cursor)
                conn.commit()

    def _create_genesis_block(self, cursor):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        action = "GENESIS_INITIALIZATION"
        payload_hash = hashlib.sha256("GEOAI_OVERLORD_GENESIS_SEED".encode("utf-8")).hexdigest().upper()
        prev_hash = "0" * 64
        raw = f"0{ts}{action}{payload_hash}{prev_hash}"
        block_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest().upper()
        cursor.execute("""
            INSERT INTO audit_blocks (block_index, timestamp, action, payload_hash, prev_hash, block_hash)
            VALUES (0, ?, ?, ?, ?, ?)
        """, (ts, action, payload_hash, prev_hash, block_hash))

    def append_block(self, action: str, data: dict):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT block_index, block_hash FROM audit_blocks ORDER BY block_index DESC LIMIT 1")
            last_index, prev_hash = cursor.fetchone()
            
            new_index = last_index + 1
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data_str = json.dumps(data, sort_keys=True)
            payload_hash = hashlib.sha256(data_str.encode("utf-8")).hexdigest().upper()
            
            raw = f"{new_index}{ts}{action}{payload_hash}{prev_hash}"
            block_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest().upper()
            
            cursor.execute("""
                INSERT INTO audit_blocks (block_index, timestamp, action, payload_hash, prev_hash, block_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (new_index, ts, action, payload_hash, prev_hash, block_hash))
            conn.commit()
            
            return {
                "block_index": new_index,
                "timestamp": ts,
                "action": action,
                "payload_hash": payload_hash,
                "prev_hash": prev_hash,
                "block_hash": block_hash
            }

    def get_latest_block(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT block_index, timestamp, action, payload_hash, prev_hash, block_hash FROM audit_blocks ORDER BY block_index DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                return {
                    "block_index": row[0],
                    "timestamp": row[1],
                    "action": row[2],
                    "payload_hash": row[3],
                    "prev_hash": row[4],
                    "block_hash": row[5]
                }
            return None
