def check_for_language(lang_code):
    """
    Check whether there is a global language file for the given language
    code. This is used to decide whether a user-provided language is
    available.

    lru_cache should have a maxsize to prevent from memory exhaustion attacks,
    as the provided language codes are taken from the HTTP request. See also
    <https://www.djangoproject.com/weblog/2007/oct/26/security-fix/>.
    """
    # First, a quick check to make sure lang_code is well-formed (#21458)
    if lang_code is None or not language_code_re.search(lang_code):
        return False
    return any(
        gettext_module.find("django", path, [to_locale(lang_code)]) is not None
        for path in all_locale_paths()
    )