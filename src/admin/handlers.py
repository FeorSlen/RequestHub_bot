from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from src.utils.admin_auth import IsAdmin
from src.admin.menu import AdminMenu
from src.admin.sql_wrapper import *
from src.admin.recourses_naive import *
from src.db_connector import DBConnector

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

AdminStates = AdminMenu.get_states()

OFFSET_KEY = "offset"
REQUEST_ID_KEY = "request_id"
REQUEST_TEXT_KEY = "request_text"


# ── Хэндлеры ────────────────────────────────────────────────

@router.message(F.text == "/start")
async def start(message: Message, state: FSMContext, db: DBConnector):
    await state.clear()
    await message.answer(ADMIN_MENU_TEXT, reply_markup=AdminMenu.get_base_manual_menu())

@router.callback_query(F.data == AdminMenu.ACTION_FALLBACK)
async def fallback(callback: CallbackQuery, state: FSMContext, db: DBConnector):
    await state.clear()
    await _load_and_show_request(callback, state, db)

@router.callback_query(F.data == AdminMenu.all_filters[AdminMenu.NON_PROCESSED_REQUEST_AMOUNT])
async def get_count_non_processed(callback: CallbackQuery, state: FSMContext, db: DBConnector):
    """Запрашивает количество необработанных обращений и выводит админу."""
    await state.clear()
    result = await db.await_execute(*get_unprocessed_amount())
    count = get_single_value(result) or 0

    await callback.message.answer(UNPROCESSED_COUNT(count), reply_markup=AdminMenu.get_base_manual_menu())
    await callback.answer()


@router.callback_query(F.data == AdminMenu.all_filters[AdminMenu.REQUEST_PROCESS])
async def process_new_request(callback: CallbackQuery, state: FSMContext, db: DBConnector):
    """Сдвигает offset циклически и загружает следующее необработанное обращение."""
    if await _get_state_value(state, REQUEST_ID_KEY) == "none":
        await _load_and_show_request(callback, state, db)
        return

    result = await db.await_execute(*get_unprocessed_amount())
    total = get_single_value(result) or 0

    if total == 0:
        await callback.message.answer(NO_UNPROCESSED, reply_markup=AdminMenu.empty_menu())
        await callback.answer()
        return

    data = await state.get_data()
    new_offset = (data.get(OFFSET_KEY, 0) + 1) % total
    await state.update_data({OFFSET_KEY: new_offset})

    await _load_and_show_request(callback, state, db)


@router.callback_query(F.data == AdminMenu.all_filters[AdminMenu.REQUEST_SPAM])
async def spam(callback: CallbackQuery, state: FSMContext, db: DBConnector):
    """Помечает все обращения с таким текстом как спам и загружает следующее."""
    spam_text = await _get_state_value(state, REQUEST_TEXT_KEY)
    await db.await_execute(*mark_text_as_spam(spam_text))

    await callback.message.answer(MARKED_AS_SPAM)
    await state.update_data({OFFSET_KEY: 0})
    await _load_and_show_request(callback, state, db)


@router.callback_query(F.data == AdminMenu.all_filters[AdminMenu.REQUEST_RESPONSE])
async def response_to_request(callback: CallbackQuery, state: FSMContext):
    """Активирует состояние написания ответа."""
    await state.set_state(AdminStates.writing_answer)
    await callback.message.answer(WRITE_ANSWER_PROMPT, reply_markup=AdminMenu.fallback_menu())
    await callback.answer()


@router.message(AdminStates.writing_answer)
async def handle_response_to_request(message: Message, state: FSMContext, db: DBConnector):
    """Сохраняет текстовый ответ админа и загружает следующее обращение."""
    print(2)
    print(message.text)
    request_id = await _get_state_value(state, REQUEST_ID_KEY)
    await db.await_execute(*update_response_to_request(message.text.strip(), request_id))

    await message.answer(ANSWER_SAVED)
    await state.update_data({OFFSET_KEY: 0})
    await state.set_state(None)
    await _load_and_show_request(message, state, db)


# ── Хэлперы ─────────────────────────────────────────────────

async def _load_and_show_request(source: CallbackQuery | Message, state: FSMContext, db: DBConnector):
    """Загружает обращение по текущему offset и отправляет админу."""
    data = await state.get_data()
    result = await db.await_execute(*get_new_request(data.get(OFFSET_KEY, 0)))

    msg = source.message if isinstance(source, CallbackQuery) else source
    row = result[0] if result else None

    if row is None:
        await state.update_data({REQUEST_ID_KEY: None, REQUEST_TEXT_KEY: None, OFFSET_KEY: 0})
        await msg.answer(NO_UNPROCESSED, reply_markup=AdminMenu.empty_menu())
    else:
        req_id, req_text = row[0], row[1]
        await state.update_data({REQUEST_ID_KEY: req_id, REQUEST_TEXT_KEY: req_text})
        await msg.answer(REQUEST_DISPLAY(req_id, req_text), reply_markup=AdminMenu.base_menu())

    if isinstance(source, CallbackQuery):
        await source.answer()


async def _get_state_value(state: FSMContext, key: str) -> str:
    data = await state.get_data()
    return data.get(key, "none")