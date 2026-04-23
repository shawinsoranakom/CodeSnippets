def do_ntranslate(singular, plural, number, translation_function):
    global _default

    t = getattr(_active, "value", None)
    if t is not None:
        return getattr(t, translation_function)(singular, plural, number)
    if _default is None:
        _default = translation(settings.LANGUAGE_CODE)
    return getattr(_default, translation_function)(singular, plural, number)