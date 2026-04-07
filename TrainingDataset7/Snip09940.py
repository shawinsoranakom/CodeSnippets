def _sqlite_sha512(text):
    if text is None:
        return None
    return sha512(text.encode()).hexdigest()