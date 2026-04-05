from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup
from typing import Dict


class Menu:
    FALLBACK: str = "⬅️ Назад"
    ACTION_FALLBACK: str = "back"

    @staticmethod
    def _btn(text: str, action: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(text=text, callback_data=action)

    @classmethod
    def fallback_menu(cls) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard = [
                [cls._btn(cls.FALLBACK, cls.ACTION_FALLBACK)]
            ]
        )

    def get_states(self) -> StatesGroup:
        raise NotImplementedError

    def get_paths_with_limit(self) -> Dict[str, int]:
        raise NotImplementedError

    def get_base_manual_menu(self) -> InlineKeyboardMarkup:
        raise NotImplementedError