def get_supported_language_variant(lang_code, strict=False):
    """
    Return the language code that's listed in supported languages, possibly
    selecting a more generic variant. Raise LookupError if nothing is found.

    If `strict` is False (the default), look for a country-specific variant
    when neither the language code nor its generic variant is found.

    The language code is truncated to a maximum length to avoid potential
    denial of service attacks.

    lru_cache should have a maxsize to prevent from memory exhaustion attacks,
    as the provided language codes are taken from the HTTP request. See also
    <https://www.djangoproject.com/weblog/2007/oct/26/security-fix/>.
    """
    if lang_code:
        # Truncate the language code to a maximum length to avoid potential
        # denial of service attacks.
        if len(lang_code) > LANGUAGE_CODE_MAX_LENGTH:
            if (
                not strict
                and (index := lang_code.rfind("-", 0, LANGUAGE_CODE_MAX_LENGTH)) > 0
            ):
                # There is a generic variant under the maximum length accepted
                # length.
                lang_code = lang_code[:index]
            else:
                raise LookupError(lang_code)
        # If 'zh-hant-tw' is not supported, try special fallback or subsequent
        # language codes i.e. 'zh-hant' and 'zh'.
        possible_lang_codes = [lang_code]
        try:
            possible_lang_codes.extend(LANG_INFO[lang_code]["fallback"])
        except KeyError:
            pass
        i = None
        while (i := lang_code.rfind("-", 0, i)) > -1:
            possible_lang_codes.append(lang_code[:i])
        generic_lang_code = possible_lang_codes[-1]
        supported_lang_codes = get_languages()

        for code in possible_lang_codes:
            if code.lower() in supported_lang_codes and check_for_language(code):
                return code
        if not strict:
            # if fr-fr is not supported, try fr-ca.
            for supported_code in supported_lang_codes:
                if supported_code.startswith(generic_lang_code + "-"):
                    return supported_code
    raise LookupError(lang_code)