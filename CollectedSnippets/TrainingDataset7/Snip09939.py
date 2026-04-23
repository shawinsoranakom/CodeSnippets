def _sqlite_sha384(text):
    if text is None:
        return None
    return sha384(text.encode()).hexdigest()