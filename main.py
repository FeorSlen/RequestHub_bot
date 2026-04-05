import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

from src.db_connector import DBConnector
from src.user.handlers import router as user_router
from src.admin.handlers import router as admin_router
from src.middleware.db_middleware import DBMiddleware
from src.middleware.rate_limit_middlware import RateLimitMiddleware
from src.user.menu import UserMenu


async def main():
    load_dotenv()
    token = os.getenv("API_TOKEN")

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()

    #обертка над базой данных для асинхронных очередей записи чтения
    db = DBConnector(loop = asyncio.get_running_loop())
    db.init()

    #немного грязно делаем бдшки DI во все хэндлеры
    dp.message.middleware(DBMiddleware(db))
    dp.callback_query.middleware(DBMiddleware(db))

    #для действий пользователя вводим rate limiting
    user_router.message.middleware(RateLimitMiddleware(UserMenu))
    user_router.callback_query.middleware(RateLimitMiddleware(UserMenu))

    dp.include_router(admin_router)
    dp.include_router(user_router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())