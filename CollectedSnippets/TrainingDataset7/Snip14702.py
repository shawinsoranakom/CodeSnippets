def reset_cache(*, setting, **kwargs):
    """
    Reset global state when LANGUAGES setting has been changed, as some
    languages should no longer be accepted.
    """
    if setting in ("LANGUAGES", "LANGUAGE_CODE"):
        check_for_language.cache_clear()
        get_languages.cache_clear()
        get_supported_language_variant.cache_clear()