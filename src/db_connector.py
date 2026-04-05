import sqlite3
import os
from .utils.thread_worker import ThreadWorker
from typing import NamedTuple, Callable, Any, Tuple
import asyncio
from functools import partial
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DATABASE_PATH")
SPAM_MARKER = "spam"

class DBConnector:
    write_conn: ThreadWorker | None
    read_conn: ThreadWorker | None

    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.write_conn = None
        self.read_conn = None
        self.loop = loop

    def init(self):
        """
        метод создает коннект к бд, переводит бд в режим WAL, создаёт базовые таблицы
        и запускает 2 воркера на чтение и запись
        """
        need_create_tables = not os.path.exists(DB_PATH) or not os.path.isfile(DB_PATH)
        temporary_writer: sqlite3.Connection = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.write_conn = SQLWriter(temporary_writer, self.loop)

        #хорошо бы в режиме WAL держать
        temporary_writer.execute("PRAGMA journal_mode=WAL;")
        temporary_writer.execute("PRAGMA synchronous=NORMAL;")
        temporary_writer.execute("PRAGMA busy_timeout=5000;")
        temporary_writer.commit()

        if need_create_tables:
            self._create_tables(temporary_writer)

        self.read_conn = SQLReader(sqlite3.connect(DB_PATH, check_same_thread=False), self.loop)


    def execute(self, query, params:Tuple[str | int, ...] = None, callback: Callable = None):
        """
        метод с наивной проверкой на тип задачи через SELECT.
        добавляет задачу в очередь воркеров и выполняет асинхронно

        :param query: sql запрос. Без нескольких запросов через
        :param params: для избежания sql инъекций, допускаем синтаксис с (?, ?)
        :param callback: каллбек на окончание выполнения операции
        """
        if query.lstrip().upper().startswith("SELECT"):
            self.read_conn.add_task(Task(query, params, callback))
        else:
            self.write_conn.add_task(Task(query, params, callback))


    async def await_execute(self, sql: str, params=None):
        """
        обертка над execute, завершаемый future для линейных вызовов
        нейронка подсказала... Т-Т
        """
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        async def _resolve(data):
            if not future.done():
                future.set_result(data)

        self.execute(sql, params, _resolve)
        return await future


    def _create_tables(self, writer: sqlite3.Connection):
        #id -> UUID
        writer.executescript("""
            
            CREATE TABLE requests (
                id TEXT PRIMARY KEY,
                request TEXT CHECK(length(request) <= 1000),
                response TEXT NOT NULL DEFAULT '' CHECK(length(response) <= 1000),
                processed INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX idx_requests_processed ON requests(processed);
                        
        """)

        writer.commit()



class Task(NamedTuple):
    sql: str
    params: Tuple[str, ...] | None
    callback: Callable[[Any | None], None] | None


class SQLWriter(ThreadWorker[Task]):
    def __init__(self, _conn: sqlite3.Connection, loop: asyncio.AbstractEventLoop):
        super().__init__()
        self._conn = _conn
        self._steps_without_save = 1000
        self._steps = 0
        self._loop = loop


    def _processing_task(self, task:Task):
        if task.params:
            cursor = self._conn.execute(task.sql, task.params)
        else:
            cursor = self._conn.execute(task.sql)

        success = cursor.rowcount > 0
        self._steps += 1

        if self._steps >= self._steps_without_save:
            self._conn.commit()
            self._steps = 0

        if task.callback:
            #in method success = (True,)
            coro = partial(task.callback, success)
            asyncio.run_coroutine_threadsafe(coro(), self._loop)

    def _on_freeze_way(self):
        self._conn.commit()


class SQLReader(ThreadWorker[Task]):
    def __init__(self, _conn: sqlite3.Connection, loop: asyncio.AbstractEventLoop):
        super().__init__()
        self._conn = _conn
        self._loop = loop

    def _processing_task(self, task:Task):
        if task.params:
            cursor = self._conn.execute(task.sql, task.params)
        else:
            cursor = self._conn.execute(task.sql)

        result = cursor.fetchall()
        cursor.close()

        if task.callback:
            coro = partial(task.callback, result)
            asyncio.run_coroutine_threadsafe(coro(), self._loop)

