def to_language(locale):
    """Turn a locale name (en_US) into a language name (en-us)."""
    p = locale.find("_")
    if p >= 0:
        return locale[:p].lower() + "-" + locale[p + 1 :].lower()
    else:
        return locale.lower()