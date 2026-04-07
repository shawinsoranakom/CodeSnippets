def _sqlite_sha224(text):
    if text is None:
        return None
    return sha224(text.encode()).hexdigest()