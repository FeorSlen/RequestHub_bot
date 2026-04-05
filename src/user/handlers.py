from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from src.user.menu import UserMenu
from src.user.recourses_naive import *
from src.user.sql_wrapper import save_text, get_request_by_id, get_single_value
from src.db_connector import DBConnector, SPAM_MARKER

import re
import uuid

router = Router()
UUID_HEX_REGEX = re.compile(r"^[0-9a-fA-F]{32}$")
UserStates = UserMenu.get_states()


@router.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    await show_menu(message, state)

@router.callback_query(F.data == UserMenu.ACTION_FALLBACK)
async def fallback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(MAIN_MENU_TEXT, reply_markup=UserMenu.get_base_manual_menu(), disable_web_page_preview=True )
    await callback.answer()


@router.callback_query(F.data == UserMenu.user_paths[UserMenu.CREATE])
async def create_request(callback: CallbackQuery, state: FSMContext):
    """
    Слушатель кнопки: `UserMenu.CREATE`. Активирует состояние пользователя связанное с:
    `handle_request(message, state, db)`
    """
    await state.set_state(UserStates.writing)
    await callback.message.answer(CREATE_REQUEST,  reply_markup=UserMenu.fallback_menu())
    await callback.answer()


@router.callback_query(F.data == UserMenu.user_paths[UserMenu.STATUS])
async def status(callback: CallbackQuery, state: FSMContext):
    """
    Слушатель кнопки: `UserMenu.STATUS`. Активирует состояние пользователя связанное с:
    `handle_request_uuid(message, state, db)`
    """
    await state.set_state(UserStates.checking)
    await callback.message.answer(CHECKING_REQUEST, reply_markup=UserMenu.fallback_menu())
    await callback.answer()


@router.message(UserStates.writing)
async def handle_request(message: Message, state: FSMContext, db: DBConnector):
    """
    Обработчик текстового обращения. Генерирует uuid и сохраняет обращение в базу данных.
    """
    text = message.text.strip()

    validators = [
        (lambda t: not t,
         "⚠️ Сообщение не может быть пустым.\n\nПожалуйста, опишите ваше обращение."),
        (lambda t: len(t) < 5,
         "⚠️ Сообщение слишком короткое.\n\nПостарайтесь описать ситуацию подробнее."),
        (lambda t: len(t) > 1000,
         "⚠️ Сообщение слишком длинное.\n\nСократите текст до 1000 символов."),
        (lambda t: t.isdigit(),
         "⚠️ Сообщение должно содержать осмысленный текст.\n\nПожалуйста, используйте слова."),
        (lambda t: ' ' not in t,
         "⚠️ Сообщение выглядит некорректно.\n\nДобавьте пробелы между словами для лучшего понимания."),
    ]

    if (error_msg := next((msg for check, msg in validators if check(text)), None)):
        await show_menu(message, state, error_msg)
        return

    uuid_str = uuid.uuid4().hex
    result = await db.await_execute(*save_text(uuid_str, message.text))
    clear_success = get_single_value(result)

    response = REQUEST_SAVED(uuid_str) if clear_success else BAD_REQUEST_SAVE
    await show_menu(message, state, response)


@router.message(UserStates.checking)
async def handle_request_uuid(message: Message, state: FSMContext, db: DBConnector):
    """
    Обработчик id обращения при запросе статуса. Валидирует id и отправляет запрос в базу данных.
    """
    user_input = message.text.strip()

    if not UUID_HEX_REGEX.match(user_input):
        await show_menu(message, state, REQUEST_STATUS_DOES_NOT_EXIST)
        return

    result = await db.await_execute(*get_request_by_id(user_input))
    clear_result = get_single_value(result)

    if clear_result and clear_result != SPAM_MARKER:
        response = REQUEST_STATUS_ANSWERING(clear_result)
    elif clear_result == "" or clear_result == SPAM_MARKER:
        response = REQUEST_STATUS_PROCESSING
    else:
        response = REQUEST_STATUS_DOES_NOT_EXIST

    await show_menu(message, state, response)


async def show_menu(message: Message, state: FSMContext, text: str = MAIN_MENU_TEXT):
    """
    Вспомогательный метод для отправки ответа пользователю с меню.
    Сбрасывает состояние пользователя.
    """
    await state.clear()
    await message.answer(text, reply_markup=UserMenu.get_base_manual_menu(), disable_web_page_preview=True )