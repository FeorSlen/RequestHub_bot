import aiosqlite
import os
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DATABASE_PATH")
SPAM_MARKER = "spam"


class DBConnector:
    def __init__(self):
        self._conn: aiosqlite.Connection | None = None

    async def init(self):
        self._conn = await aiosqlite.connect(DB_PATH)
        await self._conn.execute("PRAGMA journal_mode=WAL;")
        await self._conn.execute("PRAGMA synchronous=NORMAL;")
        await self._conn.execute("PRAGMA busy_timeout=5000;")
        await self._conn.commit()
        await self._create_tables()

    async def execute(self, sql: str, params=None):
        async with self._conn.execute(sql, params or ()) as cursor:
            if sql.lstrip().upper().startswith("SELECT"):
                return await cursor.fetchall()
            await self._conn.commit()
            return cursor.rowcount > 0

    async def close(self):
        if self._conn:
            await self._conn.close()

    async def _create_tables(self):
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id TEXT PRIMARY KEY,
                request TEXT CHECK(length(request) <= 1000),
                response TEXT NOT NULL DEFAULT '' CHECK(length(response) <= 1000),
                processed INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_requests_processed ON requests(processed)"
        )
        await self._conn.commit()
