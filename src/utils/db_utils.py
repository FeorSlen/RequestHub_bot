def get_single_value(result):
    try:
        while isinstance(result, (list, tuple)) and len(result) > 0:
            result = result[0]
        return result
    except Exception:
        return None
