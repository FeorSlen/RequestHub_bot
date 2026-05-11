import asyncio
import os
from datetime import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from dotenv import load_dotenv

from src.user.menu import UserMenu
from src.user.texts import (
    UPLOAD_PHOTO_PROMPT, PHOTO_SAVED, PHOTO_SAVED_LAST,
    PHOTO_LIMIT_REACHED, PHOTO_NOT_A_PHOTO,
)
from src.db_connector import DBConnector
from src.utils.db_utils import get_single_value, hash_user_id

load_dotenv()

router = Router()
_states = UserMenu.get_states()

_PHOTOS_DIR = os.getenv("PHOTOS_DIR", "photos")
_MAX_PHOTOS = 10
_GROUP_TIMEOUT = 0.5

# media_group_id -> list of (Message, DBConnector)
_pending: dict[str, list[tuple[Message, DBConnector]]] = {}
_tasks: dict[str, asyncio.Task] = {}


@router.callback_query(F.data == UserMenu.user_paths[UserMenu.UPLOAD_PHOTO])
async def start_photo_upload(callback: CallbackQuery, state: FSMContext):
    await state.set_state(_states.uploading_photo)
    await callback.message.answer(UPLOAD_PHOTO_PROMPT, reply_markup=UserMenu.fallback_menu())
    await callback.answer()


@router.message(_states.uploading_photo, F.photo)
async def handle_photo(message: Message, state: FSMContext, db: DBConnector):
    group_id = message.media_group_id
    if group_id:
        if group_id not in _pending:
            _pending[group_id] = []
            _tasks[group_id] = asyncio.create_task(
                _flush_group(group_id, message, state, db)
            )
        _pending[group_id].append((message, db))
    else:
        await _process_photos([message], message, state, db)


async def _flush_group(
    group_id: str, first: Message, state: FSMContext, db: DBConnector
):
    await asyncio.sleep(_GROUP_TIMEOUT)
    messages = _pending.pop(group_id, [])
    _tasks.pop(group_id, None)
    await _process_photos([m for m, _ in messages], first, state, db)


async def _process_photos(
    photos: list[Message], reply_to: Message, state: FSMContext, db: DBConnector
):
    user_hash = hash_user_id(reply_to.from_user.id)

    result = await db.execute(
        "SELECT COUNT(*) FROM photos WHERE user_hash = ?", (user_hash,)
    )
    count = get_single_value(result) or 0

    if count >= _MAX_PHOTOS:
        await state.clear()
        await reply_to.answer(PHOTO_LIMIT_REACHED, reply_markup=UserMenu.get_base_manual_menu())
        return

    user_dir = os.path.join(_PHOTOS_DIR, user_hash)
    os.makedirs(user_dir, exist_ok=True)

    to_save = photos[: _MAX_PHOTOS - count]
    saved = 0
    for msg in to_save:
        filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + f"_{saved}.jpg"
        dest = os.path.join(user_dir, filename)
        try:
            await msg.bot.download(msg.photo[-1], destination=dest)
            await db.execute(
                "INSERT INTO photos (user_hash, file_path) VALUES (?, ?)",
                (user_hash, dest),
            )
            saved += 1
        except Exception:
            pass

    if saved == 0:
        await reply_to.answer("❌ Не удалось сохранить фото. Попробуйте ещё раз.")
        return

    remaining = _MAX_PHOTOS - count - saved
    if remaining <= 0:
        await state.clear()
        await reply_to.answer(PHOTO_SAVED_LAST, reply_markup=UserMenu.get_base_manual_menu())
    else:
        await reply_to.answer(PHOTO_SAVED(remaining))


@router.message(_states.uploading_photo)
async def handle_non_photo(message: Message):
    await message.answer(PHOTO_NOT_A_PHOTO)
