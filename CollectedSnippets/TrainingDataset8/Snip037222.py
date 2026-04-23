def valid_url(url: str) -> bool:
    """
    This code is copied and pasted from:
    https://stackoverflow.com/questions/7160737/how-to-validate-a-url-in-python-malformed-or-not
    """
    try:
        result = urlparse(url)
        if result.scheme == "mailto":
            return all([result.scheme, result.path])
        return all([result.scheme, result.netloc])
    except Exception:
        return False