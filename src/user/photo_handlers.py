import os
import time
from datetime import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from dotenv import load_dotenv

from src.user.menu import UserMenu
from src.user.texts import (
    UPLOAD_PHOTO_PROMPT, PHOTO_SAVED, PHOTO_SAVED_LAST,
    PHOTO_LIMIT_REACHED, PHOTO_NOT_A_PHOTO, PHOTO_THROTTLE,
)
from src.db_connector import DBConnector
from src.utils.db_utils import get_single_value, hash_user_id

load_dotenv()

router = Router()
_states = UserMenu.get_states()

_PHOTOS_DIR = os.getenv("PHOTOS_DIR", "photos")
_MAX_PHOTOS = 10
_THROTTLE_SEC = 2
_last_upload: dict[int, float] = {}


@router.callback_query(F.data == UserMenu.user_paths[UserMenu.UPLOAD_PHOTO])
async def start_photo_upload(callback: CallbackQuery, state: FSMContext):
    await state.set_state(_states.uploading_photo)
    await callback.message.answer(UPLOAD_PHOTO_PROMPT, reply_markup=UserMenu.fallback_menu())
    await callback.answer()


@router.message(_states.uploading_photo, F.photo)
async def handle_photo(message: Message, state: FSMContext, db: DBConnector):
    user_id = message.from_user.id
    user_hash = hash_user_id(user_id)
    now = time.monotonic()

    if now - _last_upload.get(user_id, 0) < _THROTTLE_SEC:
        await message.answer(PHOTO_THROTTLE)
        return

    result = await db.execute(
        "SELECT COUNT(*) FROM photos WHERE user_hash = ?", (user_hash,)
    )
    count = get_single_value(result) or 0

    if count >= _MAX_PHOTOS:
        await state.clear()
        await message.answer(PHOTO_LIMIT_REACHED, reply_markup=UserMenu.get_base_manual_menu())
        return

    user_dir = os.path.join(_PHOTOS_DIR, user_hash)
    os.makedirs(user_dir, exist_ok=True)
    filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".jpg"
    dest = os.path.join(user_dir, filename)

    try:
        await message.bot.download(message.photo[-1], destination=dest)
    except Exception:
        await message.answer("❌ Не удалось сохранить фото. Попробуйте ещё раз.")
        return

    await db.execute(
        "INSERT INTO photos (user_hash, file_path) VALUES (?, ?)",
        (user_hash, dest),
    )
    _last_upload[user_id] = now

    remaining = _MAX_PHOTOS - count - 1
    if remaining == 0:
        await state.clear()
        await message.answer(PHOTO_SAVED_LAST, reply_markup=UserMenu.get_base_manual_menu())
    else:
        await message.answer(PHOTO_SAVED(remaining))


@router.message(_states.uploading_photo)
async def handle_non_photo(message: Message):
    await message.answer(PHOTO_NOT_A_PHOTO)
