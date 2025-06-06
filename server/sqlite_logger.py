import os
import sqlite3
from datetime import datetime
from pathlib import Path


class SQLiteLogger:

    def __init__(self, db_path: str = "/data/logs.db"):
        # パス配下のディレクトリが無ければ作成
        Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_db()

    # 開始レコードを追加し、行 ID を返却
    def log_start(
        self,
        start_time: str,
        client_ip: str,
        operation: int,
        file_name: str,
        file_size: int,
        media_type: str,
    ) -> int:
      
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO logs
                  (start_time, end_time, client_ip, operation, file_name,
                   file_size, media_type)
                VALUES (?, NULL, ?, ?, ?, ?, ?)
                """,
                (
                    start_time,
                    client_ip,
                    operation,
                    file_name,
                    file_size,
                    media_type,
                ),
            )
            conn.commit()
            return cur.lastrowid

    # 終了時刻を更新
    def log_end(self, row_id: int, end_time: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE logs SET end_time = ? WHERE id = ?",
                (end_time, row_id),
            )
            conn.commit()

    # 初回呼び出し時にテーブルを作成
    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS logs (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT,
                    end_time   TEXT,
                    client_ip  TEXT,
                    operation  INTEGER,
                    file_name  TEXT,
                    file_size  INTEGER,
                    media_type TEXT
                )
                """
            )
            conn.commit()


_default_logger = SQLiteLogger(os.environ.get("SQLITE_DB_PATH", "/data/logs.db"))

log_start = _default_logger.log_start
log_end   = _default_logger.log_end
