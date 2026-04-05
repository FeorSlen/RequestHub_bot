from typing import ClassVar
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.utils.menu import Menu


class AdminMenu(Menu):
    REQUEST_PROCESS = "📩 Новое обращение"
    REQUEST_SPAM = "🚫 Отправить в спам"
    REQUEST_RESPONSE = "✍️ Ответить на обращение"
    NON_PROCESSED_REQUEST_AMOUNT = "📊 Количество необработанных обращений"

    all_filters: ClassVar[dict[str, str]] = {
        REQUEST_PROCESS: "process",
        REQUEST_SPAM: "spam",
        REQUEST_RESPONSE: "response",
        NON_PROCESSED_REQUEST_AMOUNT: "amount"
    }

    class AdminStates(StatesGroup):
        writing_answer = State()

    states = AdminStates()

    @staticmethod
    def __btn(key: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=key,
            callback_data=AdminMenu.all_filters[key]
        )

    @staticmethod
    def _row(btn1: str, btn2: str):
        return [
            AdminMenu.__btn(btn1),
            AdminMenu.__btn(btn2)
        ]

    @classmethod
    def empty_menu(cls) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                cls._row(cls.REQUEST_PROCESS, cls.NON_PROCESSED_REQUEST_AMOUNT)
            ]
        )

    @classmethod
    def base_menu(cls) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                cls._row(cls.REQUEST_PROCESS, cls.NON_PROCESSED_REQUEST_AMOUNT),
                cls._row(cls.REQUEST_SPAM, cls.REQUEST_RESPONSE),
            ]
        )

    @classmethod
    def get_base_manual_menu(cls) -> InlineKeyboardMarkup:
        return cls.empty_menu()

    @classmethod
    def get_states(cls) -> StatesGroup:
        return cls.states