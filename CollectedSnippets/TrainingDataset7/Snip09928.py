def _sqlite_md5(text):
    if text is None:
        return None
    return md5(text.encode()).hexdigest()