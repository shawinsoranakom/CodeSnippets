def get_supported_language_variant(lang_code, strict=False):
    if lang_code and lang_code.lower() == settings.LANGUAGE_CODE.lower():
        return lang_code
    else:
        raise LookupError(lang_code)