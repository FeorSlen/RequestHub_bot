from typing import Tuple


def save_text(uuid: str, text: str) -> Tuple[str, tuple]:
    return (
        "INSERT INTO requests (id, request) VALUES (?, ?)",
        (uuid, text),
    )


def get_request_by_id(uuid: str) -> Tuple[str, tuple]:
    return (
        "SELECT response FROM requests WHERE id = ? LIMIT 1",
        (uuid,),
    )


def get_single_value(value):
    try:
        while isinstance(value, (list, tuple)) and len(value) > 0:
            value = value[0]
        return value
    except Exception:
        return None