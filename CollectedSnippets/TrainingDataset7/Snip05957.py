def get_select2_language():
    lang_code = get_language()
    supported_code = SELECT2_TRANSLATIONS.get(lang_code)
    if supported_code is None and lang_code is not None:
        # If 'zh-hant-tw' is not supported, try subsequent language codes i.e.
        # 'zh-hant' and 'zh'.
        i = None
        while (i := lang_code.rfind("-", 0, i)) > -1:
            if supported_code := SELECT2_TRANSLATIONS.get(lang_code[:i]):
                return supported_code
    return supported_code