def _sqlite_sha256(text):
    if text is None:
        return None
    return sha256(text.encode()).hexdigest()