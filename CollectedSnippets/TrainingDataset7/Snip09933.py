def _sqlite_repeat(text, count):
    if text is None or count is None:
        return None
    return text * count