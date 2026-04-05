from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from typing import ClassVar, Dict

from src.utils.menu import Menu


class UserMenu(Menu):
    CREATE: ClassVar[str] = "Написать обращение ✍️"
    STATUS: ClassVar[str] = "Статус обращений 📊"

    ACTION_CREATE: ClassVar[str] = "request"
    ACTION_STATUS: ClassVar[str] = "status"

    class UserStates(StatesGroup):
        writing: State = State()
        checking: State = State()

    states = UserStates()

    user_paths: ClassVar[Dict[str, str]] = {
        CREATE: ACTION_CREATE,
        STATUS: ACTION_STATUS,
    }

    paths_with_limit: ClassVar[Dict[str, int]] = {
        ACTION_CREATE: 5,
        ACTION_STATUS: 100,

        "UserStates:writing": 5,
        "UserStates:checking": 10,
    }

    @classmethod
    def user_menu(cls) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [cls._btn(text, action) for text, action in cls.user_paths.items()]
            ]
        )

    @classmethod
    def get_states(cls) -> StatesGroup:
        return cls.states

    @classmethod
    def get_paths_with_limit(cls) -> Dict[str, int]:
        return cls.paths_with_limit

    @classmethod
    def get_base_manual_menu(cls) -> InlineKeyboardMarkup:
        return cls.user_menu()