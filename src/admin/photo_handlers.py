import io
import os
import zipfile
from dotenv import load_dotenv

from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile

from src.utils.admin_auth import IsAdmin
from src.admin.menu import AdminMenu

load_dotenv()

router = Router()
router.callback_query.filter(IsAdmin())

_PHOTOS_DIR = os.getenv("PHOTOS_DIR", "photos")


@router.callback_query(F.data == AdminMenu.all_filters[AdminMenu.DOWNLOAD_PHOTOS])
async def download_photos_archive(callback: CallbackQuery):
    await callback.answer("⏳ Формирую архив...")

    if not os.path.exists(_PHOTOS_DIR):
        await callback.message.answer("📂 Фото ещё не загружались.")
        return

    buf = io.BytesIO()
    count = 0
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(_PHOTOS_DIR):
            for fname in sorted(files):
                if fname.endswith(".jpg"):
                    fpath = os.path.join(root, fname)
                    arcname = os.path.relpath(fpath, _PHOTOS_DIR)
                    zf.write(fpath, arcname)
                    count += 1

    if count == 0:
        await callback.message.answer("📂 Фото ещё не загружались.")
        return

    buf.seek(0)
    await callback.message.answer_document(
        BufferedInputFile(buf.read(), filename="photos.zip"),
        caption=f"📦 Архив фото: {count} файлов",
    )
