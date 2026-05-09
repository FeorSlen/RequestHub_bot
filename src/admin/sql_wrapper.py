from src.db_connector import SPAM_MARKER


def get_unprocessed_amount():
    return "SELECT COUNT(*) FROM requests WHERE processed = 0", None


def get_new_request(offset: int):
    return (
        "SELECT id, request FROM requests WHERE processed = 0 "
        "ORDER BY created_at ASC LIMIT 1 OFFSET ?",
        (offset,),
    )


def update_response_to_request(response: str, request_id: str):
    return (
        "UPDATE requests SET response = ?, processed = 1 WHERE id = ?",
        (response, request_id),
    )


def mark_text_as_spam(text: str):
    return (
        "UPDATE requests SET response = ?, processed = 1 WHERE request = ? AND processed = 0",
        (SPAM_MARKER, text),
    )
