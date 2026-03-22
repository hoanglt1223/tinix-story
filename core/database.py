"""
Module quản lý cơ sở dữ liệu - Hỗ trợ SQLite local và Turso cloud
Sử dụng libsql SDK, tương thích SQLite syntax.
Nếu TURSO_DATABASE_URL được set → kết nối Turso cloud
Nếu không → dùng SQLite file local (dev mode)
"""
import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DB_DIR = "data"
# Kiểm tra writable filesystem; nếu read-only (Vercel) → dùng /tmp
try:
    os.makedirs(DB_DIR, exist_ok=True)
    # Test ghi thực tế (thư mục có thể tồn tại nhưng read-only)
    _test_file = os.path.join(DB_DIR, ".write_test")
    with open(_test_file, "w") as f:
        f.write("ok")
    os.remove(_test_file)
except OSError:
    DB_DIR = os.path.join("/tmp", "data")
    os.makedirs(DB_DIR, exist_ok=True)
DB_FILE = os.path.join(DB_DIR, "tinix_story.db")

# Turso cloud env vars
TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL", "")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "")

_connection = None


class DictRow:
    """Wrapper giúp truy cập row theo tên cột như sqlite3.Row"""
    def __init__(self, cursor_description, row_data):
        self._keys = [desc[0] for desc in cursor_description] if cursor_description else []
        self._data = row_data if row_data else ()

    def __getitem__(self, key):
        if isinstance(key, str):
            try:
                idx = self._keys.index(key)
                return self._data[idx]
            except (ValueError, IndexError):
                raise KeyError(key)
        return self._data[key]

    def get(self, key, default=None):
        try:
            return self[key]
        except (KeyError, IndexError):
            return default

    def keys(self):
        return self._keys


class DictCursor:
    """Cursor wrapper trả về DictRow thay vì tuple"""
    def __init__(self, real_cursor):
        self._cursor = real_cursor

    @property
    def description(self):
        return self._cursor.description

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    def execute(self, sql, params=None):
        if params:
            self._cursor.execute(sql, params)
        else:
            self._cursor.execute(sql)
        return self

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        return DictRow(self._cursor.description, row)

    def fetchall(self):
        rows = self._cursor.fetchall()
        desc = self._cursor.description
        return [DictRow(desc, r) for r in rows]

    def fetchmany(self, size=None):
        rows = self._cursor.fetchmany(size) if size else self._cursor.fetchmany()
        desc = self._cursor.description
        return [DictRow(desc, r) for r in rows]

    def close(self):
        self._cursor.close()


class ConnectionWrapper:
    """
    Wrapper cho kết nối DB, cung cấp API tương thích sqlite3.
    Tự động wrap cursor để trả về DictRow.
    """
    def __init__(self, real_conn):
        self._conn = real_conn

    def execute(self, sql, params=None):
        cursor = self._conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        return DictCursor(cursor)

    def cursor(self):
        return DictCursor(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()

    def sync(self):
        """Sync embedded replica với Turso cloud (no-op cho local SQLite)"""
        if hasattr(self._conn, 'sync'):
            self._conn.sync()


def _create_connection():
    """Tạo kết nối DB dựa trên env vars"""
    import libsql_experimental as libsql

    if TURSO_DATABASE_URL and TURSO_AUTH_TOKEN:
        # Turso cloud với embedded replica (local cache + cloud sync)
        logger.info(f"Connecting to Turso: {TURSO_DATABASE_URL[:40]}...")
        conn = libsql.connect(
            f"file:{DB_FILE}",
            sync_url=TURSO_DATABASE_URL,
            auth_token=TURSO_AUTH_TOKEN,
        )
        conn.sync()
        logger.info("Turso embedded replica connected and synced")
    elif TURSO_DATABASE_URL:
        # Turso cloud only (không có local replica)
        logger.info(f"Connecting to Turso (remote only): {TURSO_DATABASE_URL[:40]}...")
        conn = libsql.connect(
            TURSO_DATABASE_URL,
            auth_token=TURSO_AUTH_TOKEN or "",
        )
        logger.info("Turso remote connected")
    else:
        # Local SQLite file (dev mode)
        logger.info(f"Connecting to local SQLite: {DB_FILE}")
        conn = libsql.connect(f"file:{DB_FILE}")
        logger.info("Local SQLite connected")

    return conn


def get_db() -> ConnectionWrapper:
    """Lấy kết nối DB singleton"""
    global _connection
    if _connection is None:
        raw_conn = _create_connection()
        _connection = ConnectionWrapper(raw_conn)
        # libsql hỗ trợ PRAGMA tương tự SQLite
        _connection.execute("PRAGMA foreign_keys=ON")
        init_db(_connection)
        logger.info("Database ready")
    return _connection


# === Schema DDL statements (tách riêng vì libsql không hỗ trợ executescript) ===
_DDL_STATEMENTS = [
    """CREATE TABLE IF NOT EXISTS config (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS backends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        type TEXT NOT NULL,
        base_url TEXT NOT NULL,
        api_key TEXT NOT NULL DEFAULT '',
        model TEXT NOT NULL DEFAULT '',
        enabled INTEGER NOT NULL DEFAULT 1,
        timeout INTEGER NOT NULL DEFAULT 30,
        retry_times INTEGER NOT NULL DEFAULT 3,
        is_default INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS config_backups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS response_cache (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        ttl INTEGER NOT NULL DEFAULT 3600
    )""",
    """CREATE TABLE IF NOT EXISTS generation_cache (
        project_id TEXT PRIMARY KEY,
        data TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS chapter_summaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT NOT NULL,
        chapter_num INTEGER NOT NULL,
        summary TEXT NOT NULL,
        generated_at TEXT NOT NULL,
        UNIQUE(project_id, chapter_num)
    )""",
    """CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        genre TEXT NOT NULL DEFAULT '',
        sub_genres TEXT NOT NULL DEFAULT '[]',
        character_setting TEXT NOT NULL DEFAULT '',
        world_setting TEXT NOT NULL DEFAULT '',
        plot_idea TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS chapters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT NOT NULL,
        num INTEGER NOT NULL,
        title TEXT NOT NULL DEFAULT '',
        desc TEXT NOT NULL DEFAULT '',
        content TEXT NOT NULL DEFAULT '',
        word_count INTEGER NOT NULL DEFAULT 0,
        generated_at TEXT,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        UNIQUE(project_id, num)
    )""",
]


def init_db(conn=None) -> None:
    """Tạo tất cả bảng nếu chưa có"""
    if conn is None:
        conn = get_db()

    for ddl in _DDL_STATEMENTS:
        conn.execute(ddl)

    # Đảm bảo schema cũ được cập nhật
    try:
        conn.execute("ALTER TABLE projects ADD COLUMN sub_genres TEXT NOT NULL DEFAULT '[]'")
    except Exception:
        pass  # Đã có cột

    conn.commit()
    logger.info("Database tables initialized")


def migrate_from_files() -> str:
    """
    Đọc dữ liệu cũ từ file JSON → insert vào DB.
    Không xóa file cũ (giữ lại để phòng lỗi).

    Returns:
        Báo cáo migration
    """
    conn = get_db()
    report = []
    now = datetime.now().isoformat()

    # 1. Migrate config
    config_file = os.path.join("config", "novel_tool_config.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            backends = data.get("backends", [])
            migrated_backends = 0
            for b in backends:
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO backends
                        (name, type, base_url, api_key, model, enabled, timeout, retry_times, is_default, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        b.get("name", ""),
                        b.get("type", "openai"),
                        b.get("base_url", ""),
                        b.get("api_key", ""),
                        b.get("model", ""),
                        1 if b.get("enabled", True) else 0,
                        b.get("timeout", 30),
                        b.get("retry_times", 3),
                        1 if b.get("is_default", False) else 0,
                        now, now
                    ))
                    migrated_backends += 1
                except Exception as e:
                    logger.warning(f"Migrate backend failed: {e}")

            gen = data.get("generation", {})
            if gen:
                conn.execute(
                    "INSERT OR REPLACE INTO config (key, value, updated_at) VALUES (?, ?, ?)",
                    ("generation", json.dumps(gen, ensure_ascii=False), now)
                )

            version = data.get("version", "4.0.0")
            conn.execute(
                "INSERT OR REPLACE INTO config (key, value, updated_at) VALUES (?, ?, ?)",
                ("version", version, now)
            )

            conn.commit()
            report.append(f"✅ Config: {migrated_backends} backends migrated")
        except Exception as e:
            report.append(f"❌ Config migration failed: {e}")
    else:
        report.append("⏭ Config file not found, skipped")

    # 2. Migrate config backups
    backup_dir = os.path.join("config", "backups")
    if os.path.exists(backup_dir):
        migrated_backups = 0
        for fname in os.listdir(backup_dir):
            fpath = os.path.join(backup_dir, fname)
            if fname.endswith(".json") and os.path.isfile(fpath):
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        backup_data = f.read()
                    created = now
                    if fname.startswith("backup_"):
                        parts = fname.replace("backup_", "").replace(".json", "")
                        try:
                            created = datetime.strptime(parts, "%Y%m%d_%H%M%S").isoformat()
                        except ValueError:
                            pass
                    conn.execute(
                        "INSERT INTO config_backups (data, created_at) VALUES (?, ?)",
                        (backup_data, created)
                    )
                    migrated_backups += 1
                except Exception as e:
                    logger.warning(f"Migrate backup {fname} failed: {e}")
        conn.commit()
        report.append(f"✅ Config backups: {migrated_backups} backups migrated")

    # 3. Migrate response cache
    cache_file = os.path.join("cache", "response_cache.json")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            migrated_cache = 0
            for k, v in cache_data.items():
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO response_cache (key, value, timestamp, ttl) VALUES (?, ?, ?, ?)",
                        (k, v.get("value", ""), v.get("timestamp", now), int(v.get("ttl", 3600)))
                    )
                    migrated_cache += 1
                except Exception as e:
                    logger.warning(f"Migrate cache entry failed: {e}")
            conn.commit()
            report.append(f"✅ Response cache: {migrated_cache} entries migrated")
        except Exception as e:
            report.append(f"❌ Response cache migration failed: {e}")
    else:
        report.append("⏭ Response cache not found, skipped")

    # 4. Migrate generation cache
    gen_cache_dir = Path("cache/generation")
    if gen_cache_dir.exists():
        migrated_gen = 0
        for cache_file in gen_cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    gen_data = f.read()
                conn.execute(
                    "INSERT OR IGNORE INTO generation_cache (project_id, data, updated_at) VALUES (?, ?, ?)",
                    (cache_file.stem, gen_data, now)
                )
                migrated_gen += 1
            except Exception as e:
                logger.warning(f"Migrate generation cache {cache_file.name} failed: {e}")
        conn.commit()
        report.append(f"✅ Generation cache: {migrated_gen} entries migrated")

    # 5. Migrate chapter summaries
    summary_dir = Path("cache/summaries")
    if summary_dir.exists():
        migrated_summaries = 0
        for project_dir in summary_dir.iterdir():
            if not project_dir.is_dir():
                continue
            for summary_file in project_dir.glob("*.json"):
                try:
                    with open(summary_file, "r", encoding="utf-8") as f:
                        summary_data = json.load(f)
                    conn.execute("""
                        INSERT OR IGNORE INTO chapter_summaries
                        (project_id, chapter_num, summary, generated_at)
                        VALUES (?, ?, ?, ?)
                    """, (
                        project_dir.name,
                        summary_data.get("chapter_num", int(summary_file.stem)),
                        summary_data.get("summary", ""),
                        summary_data.get("generated_at", now)
                    ))
                    migrated_summaries += 1
                except Exception as e:
                    logger.warning(f"Migrate summary {summary_file} failed: {e}")
        conn.commit()
        report.append(f"✅ Chapter summaries: {migrated_summaries} entries migrated")

    # 6. Migrate projects
    projects_dir = "projects"
    if os.path.exists(projects_dir):
        migrated_projects = 0
        for project_id in os.listdir(projects_dir):
            project_path = os.path.join(projects_dir, project_id)
            if not os.path.isdir(project_path):
                continue
            metadata_file = os.path.join(project_path, "metadata.json")
            if not os.path.exists(metadata_file):
                continue
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)

                conn.execute("""
                    INSERT OR IGNORE INTO projects
                    (id, title, genre, character_setting, world_setting, plot_idea, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metadata.get("id", project_id),
                    metadata.get("title", ""),
                    metadata.get("genre", ""),
                    metadata.get("character_setting", ""),
                    metadata.get("world_setting", ""),
                    metadata.get("plot_idea", ""),
                    metadata.get("created_at", now),
                    metadata.get("updated_at", now)
                ))

                for ch in metadata.get("chapters", []):
                    try:
                        conn.execute("""
                            INSERT OR IGNORE INTO chapters
                            (project_id, num, title, desc, content, word_count, generated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            metadata.get("id", project_id),
                            ch.get("num", 0),
                            ch.get("title", ""),
                            ch.get("desc", ""),
                            ch.get("content", ""),
                            ch.get("word_count", 0),
                            ch.get("generated_at")
                        ))
                    except Exception as e:
                        logger.warning(f"Migrate chapter {ch.get('num')} failed: {e}")

                migrated_projects += 1
            except Exception as e:
                logger.warning(f"Migrate project {project_id} failed: {e}")

        conn.commit()
        report.append(f"✅ Projects: {migrated_projects} projects migrated")
    else:
        report.append("⏭ Projects directory not found, skipped")

    # Sync với Turso cloud nếu đang dùng embedded replica
    _connection.sync()

    result = "\n".join(report)
    logger.info(f"Migration complete:\n{result}")
    return result
