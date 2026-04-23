def get_format_modules(lang=None):
    """Return a list of the format modules found."""
    if lang is None:
        lang = get_language()
    if lang not in _format_modules_cache:
        _format_modules_cache[lang] = list(
            iter_format_modules(lang, settings.FORMAT_MODULE_PATH)
        )
    return _format_modules_cache[lang]