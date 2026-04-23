def to_key(key: Optional[Key]) -> Optional[str]:
    if key is None:
        return None
    else:
        return str(key)