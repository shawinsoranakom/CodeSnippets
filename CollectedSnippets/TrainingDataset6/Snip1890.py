def lang_callback(lang: str | None) -> str | None:
    if lang is None:
        return None
    lang = lang.lower()
    return lang