import json
import sqlite3
import struct
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class SpatialDBManager:
    """Räumliche Datenbankverwaltung auf Basis von SQLite mit R-Tree Indizierung.

    Optimiert für massenhafte Punktwolken-, Trassierungs- und Vektordaten ohne vollständiges Laden in den Arbeitsspeicher.
    """

    def __init__(self, db_path: str | Path = "geo_spatial.db") -> None:
        """Initialisiert die Datenbankverbindung und richtet räumliche Indizes ein."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Liefert eine performante SQLite-Verbindung mit aktivierter R-Tree Unterstützung."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA page_size = 65536;")
        conn.execute("PRAGMA cache_size = -64000;")  # ~64 MB RAM Cache
        return conn

    def _init_database(self) -> None:
        """Erzeugt alle erforderlichen Tabellen und räumlichen R-Tree Indizes."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS pointcloud_datasets (
                    dataset_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    filepath TEXT NOT NULL UNIQUE,
                    srs_wkt TEXT NOT NULL,
                    point_count INTEGER NOT NULL,
                    min_x REAL NOT NULL, max_x REAL NOT NULL,
                    min_y REAL NOT NULL, max_y REAL NOT NULL,
                    min_z REAL NOT NULL, max_z REAL NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS spatial_chunks (
                    chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id INTEGER NOT NULL,
                    point_count INTEGER NOT NULL,
                    binary_data BLOB NOT NULL,
                    FOREIGN KEY (dataset_id) REFERENCES pointcloud_datasets(dataset_id) ON DELETE CASCADE
                );
                """
            )

            cursor.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS rtree_spatial_chunks USING rtree(
                    id INTEGER PRIMARY KEY,
                    min_x REAL, max_x REAL,
                    min_y REAL, max_y REAL,
                    min_z REAL, max_z REAL
                );
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS vector_features (
                    feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    layer_name TEXT NOT NULL,
                    feature_type TEXT NOT NULL,
                    attributes_json TEXT NOT NULL,
                    geometry_geojson TEXT NOT NULL
                );
                """
            )

            cursor.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS rtree_vector_features USING rtree(
                    id INTEGER PRIMARY KEY,
                    min_x REAL, max_x REAL,
                    min_y REAL, max_y REAL
                );
                """
            )

            conn.commit()

    def register_pointcloud_dataset(
        self,
        filename: str,
        filepath: str,
        srs_wkt: str,
        point_count: int,
        bounds: Tuple[float, float, float, float, float, float],
    ) -> int:
        min_x, max_x, min_y, max_y, min_z, max_z = bounds
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO pointcloud_datasets 
                (filename, filepath, srs_wkt, point_count, min_x, max_x, min_y, max_y, min_z, max_z)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(filepath) DO UPDATE SET
                    point_count = excluded.point_count,
                    min_x = excluded.min_x, max_x = excluded.max_x,
                    min_y = excluded.min_y, max_y = excluded.max_y,
                    min_z = excluded.min_z, max_z = excluded.max_z;
                """,
                (
                    filename,
                    filepath,
                    srs_wkt,
                    point_count,
                    min_x,
                    max_x,
                    min_y,
                    max_y,
                    min_z,
                    max_z,
                ),
            )
            conn.commit()

            cursor.execute(
                "SELECT dataset_id FROM pointcloud_datasets WHERE filepath = ?;",
                (filepath,),
            )
            return int(cursor.fetchone()["dataset_id"])

    def insert_spatial_chunk(
        self,
        dataset_id: int,
        bounds: Tuple[float, float, float, float, float, float],
        binary_data: bytes,
        point_count: int,
    ) -> int:
        min_x, max_x, min_y, max_y, min_z, max_z = bounds

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION;")

            cursor.execute(
                """
                INSERT INTO spatial_chunks (dataset_id, point_count, binary_data)
                VALUES (?, ?, ?);
                """,
                (dataset_id, point_count, binary_data),
            )
            chunk_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO rtree_spatial_chunks (id, min_x, max_x, min_y, max_y, min_z, max_z)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (chunk_id, min_x, max_x, min_y, max_y, min_z, max_z),
            )

            conn.commit()
            return int(chunk_id)

    def query_chunks_by_bounding_box(
        self,
        min_x: float,
        max_x: float,
        min_y: float,
        max_y: float,
        min_z: float = -99999.0,
        max_z: float = 99999.0,
    ) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT c.chunk_id, c.dataset_id, c.point_count, c.binary_data,
                       r.min_x, r.max_x, r.min_y, r.max_y, r.min_z, r.max_z
                FROM rtree_spatial_chunks r
                JOIN spatial_chunks c ON r.id = c.chunk_id
                WHERE r.min_x <= ? AND r.max_x >= ?
                  AND r.min_y <= ? AND r.max_y >= ?
                  AND r.min_z <= ? AND r.max_z >= ?;
                """,
                (max_x, min_x, max_y, min_y, max_z, min_z),
            )
            rows = cursor.fetchall()

            results = []
            for r in rows:
                results.append(
                    {
                        "chunk_id": r["chunk_id"],
                        "dataset_id": r["dataset_id"],
                        "point_count": r["point_count"],
                        "binary_data": r["binary_data"],
                        "bounds": (
                            r["min_x"],
                            r["max_x"],
                            r["min_y"],
                            r["max_y"],
                            r["min_z"],
                            r["max_z"],
                        ),
                    }
                )
            return results

    def insert_vector_feature(
        self,
        layer_name: str,
        feature_type: str,
        attributes: Dict[str, Any],
        geojson_geom: Dict[str, Any],
        bounds_2d: Tuple[float, float, float, float],
    ) -> int:
        min_x, max_x, min_y, max_y = bounds_2d
        attr_json = json.dumps(attributes, ensure_ascii=False)
        geom_json = json.dumps(geojson_geom, ensure_ascii=False)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION;")

            cursor.execute(
                """
                INSERT INTO vector_features (layer_name, feature_type, attributes_json, geometry_geojson)
                VALUES (?, ?, ?, ?);
                """,
                (layer_name, feature_type, attr_json, geom_json),
            )
            feature_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO rtree_vector_features (id, min_x, max_x, min_y, max_y)
                VALUES (?, ?, ?, ?, ?);
                """,
                (feature_id, min_x, max_x, min_y, max_y),
            )

            conn.commit()
            return int(feature_id)

    def query_vector_features_2d(
        self, min_x: float, max_x: float, min_y: float, max_y: float, layer_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if layer_name:
                cursor.execute(
                    """
                    SELECT v.feature_id, v.layer_name, v.feature_type, v.attributes_json, v.geometry_geojson
                    FROM rtree_vector_features r
                    JOIN vector_features v ON r.id = v.feature_id
                    WHERE r.min_x <= ? AND r.max_x >= ?
                      AND r.min_y <= ? AND r.max_y >= ?
                      AND v.layer_name = ?;
                    """,
                    (max_x, min_x, max_y, min_y, layer_name),
                )
            else:
                cursor.execute(
                    """
                    SELECT v.feature_id, v.layer_name, v.feature_type, v.attributes_json, v.geometry_geojson
                    FROM rtree_vector_features r
                    JOIN vector_features v ON r.id = v.feature_id
                    WHERE r.min_x <= ? AND r.max_x >= ?
                      AND r.min_y <= ? AND r.max_y >= ?;
                    """,
                    (max_x, min_x, max_y, min_y),
                )

            rows = cursor.fetchall()
            results = []
            for r in rows:
                results.append(
                    {
                        "feature_id": r["feature_id"],
                        "layer_name": r["layer_name"],
                        "feature_type": r["feature_type"],
                        "attributes": json.loads(r["attributes_json"]),
                        "geometry": json.loads(r["geometry_geojson"]),
                    }
                )
            return results

    def close(self) -> None:
        pass