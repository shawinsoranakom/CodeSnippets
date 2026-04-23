def check_setting_languages_bidi(app_configs, **kwargs):
    """Error if LANGUAGES_BIDI setting is invalid."""
    return [
        Error(E003.msg.format(tag), id=E003.id)
        for tag in settings.LANGUAGES_BIDI
        if not isinstance(tag, str) or not language_code_re.match(tag)
    ]