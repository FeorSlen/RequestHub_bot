import time
from typing import Dict
import asyncio

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from src.utils.menu import Menu


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, menu: Menu):
        super().__init__()
        self.paths_with_limit = menu.get_paths_with_limit()
        self.users = {}

        asyncio.create_task(self._daily_reset())

    async def _daily_reset(self):
        while True:
            now = time.localtime()
            # Время до полуночи
            seconds_until_midnight = (24 - now.tm_hour - 1) * 3600 + (60 - now.tm_min - 1) * 60 + (60 - now.tm_sec)
            await asyncio.sleep(seconds_until_midnight + 1)
            self.users.clear()
            print("[RateLimit] Сброс всех лимитов на сегодня")

    async def __call__(self, handler, event, data):
        user_id = str(getattr(event.from_user, "id", None))
        path = None

        #проверяем путь, это обработка нажатий кнопок
        if isinstance(event, Message):
            path = event.text
        elif isinstance(event, CallbackQuery):
            path = event.data

        #проверяем состояния, подача обращения или запрос инфы по обращению блокируются тут
        state: FSMContext = data.get("state")
        if (path not in self.paths_with_limit.keys()) and (state is not None):
            path = await state.get_state()

        if path is None:
            return await handler(event, data)

        limit = self.paths_with_limit.get(path)

        if limit is not None:
            user_events = self.users.get(user_id + path, 0)
            if user_events < limit:
                self.users[user_id + path] = user_events + 1
                return await handler(event, data)
            else:
                await event.answer("Лимит запросов на сегодня исчерпан")

                if isinstance(event, CallbackQuery):
                    await event.answer()

                return None
        else:
            return await handler(event, data)