from time import sleep

import threading
import queue
from typing import TypeVar, Generic


T = TypeVar("T")
class ThreadWorker(Generic[T]):
    def __init__(self):
        self._queue: queue.Queue = queue.Queue()
        self._thread: threading.Thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._running: bool = False

    def _worker_loop(self):
        while self._running:
            try:
                task: T = self._queue.get_nowait()
            except queue.Empty:
                self._on_freeze_way()
                sleep(0.5)
                continue

            try:
                self._processing_task(task)
            except Exception as e:
                print(e)
            finally:
                self._queue.task_done()

    def _processing_task(self, task: T):
        raise NotImplementedError

    def _on_freeze_way(self):
        pass

    def add_task(self, task):
        self._queue.put(task)

        if not self._running:
            self._running = True
            self._thread.start()
