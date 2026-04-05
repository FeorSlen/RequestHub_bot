import hmac
import hashlib
from aiogram.filters import Filter
import os
import secrets

SECRET = secrets.token_hex(32)

def _make_hash(user_id: str) -> str:
    return hmac.new(
        SECRET.encode(),
        user_id.encode(),
        hashlib.sha256
    ).hexdigest()


ADMIN_HASHES = {
    _make_hash(uid)
    for uid in os.getenv("ADMIN_TG_IDS", "").split(",")
}

class IsAdmin(Filter):
    async def __call__(self, message):
        return _make_hash(str(message.from_user.id)) in ADMIN_HASHES