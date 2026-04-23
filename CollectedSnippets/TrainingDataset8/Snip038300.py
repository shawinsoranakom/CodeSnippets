def calc_md5(s: str) -> str:
    """Return the md5 hash of the given string."""
    h = hashlib.new("md5")
    h.update(s.encode("utf-8"))
    return h.hexdigest()