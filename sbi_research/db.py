from __future__ import annotations
import json, sqlite3
from pathlib import Path
from .schema import SCHEMA


def connect(path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialise(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as conn:
        conn.executescript(SCHEMA)


def json_value(value, default):
    return json.dumps(default if value is None else value, ensure_ascii=False, separators=(",", ":"))


def rows(conn: sqlite3.Connection, sql: str, params=()):
    return [dict(row) for row in conn.execute(sql, params)]
