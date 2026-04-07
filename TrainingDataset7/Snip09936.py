def _sqlite_sha1(text):
    if text is None:
        return None
    return sha1(text.encode()).hexdigest()