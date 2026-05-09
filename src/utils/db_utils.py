import hashlib
import hmac
import os
from dotenv import load_dotenv

load_dotenv()
_PHOTO_SECRET = os.getenv("PHOTO_USER_SECRET", "").encode()


def hash_user_id(user_id: int) -> str:
    return hmac.new(_PHOTO_SECRET, str(user_id).encode(), hashlib.sha256).hexdigest()[:16]


def get_single_value(result):
    try:
        while isinstance(result, (list, tuple)) and len(result) > 0:
            result = result[0]
        return result
    except Exception:
        return None
