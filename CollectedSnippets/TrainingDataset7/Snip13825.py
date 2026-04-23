def language_changed(*, setting, **kwargs):
    if setting in {"LANGUAGES", "LANGUAGE_CODE", "LOCALE_PATHS"}:
        from django.utils.translation import trans_real

        trans_real._default = None
        trans_real._active = Local()
    if setting in {"LANGUAGES", "LOCALE_PATHS"}:
        from django.utils.translation import trans_real

        trans_real._translations = {}
        trans_real.check_for_language.cache_clear()