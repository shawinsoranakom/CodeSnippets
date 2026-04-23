def _get_translation_source(stack_level: int, module: str = '', lang: str = '', default_lang: str = '') -> tuple[str, str]:
    if not (module and lang):
        frame = inspect.currentframe()
        for _index in range(stack_level + 1):
            frame = frame.f_back
        lang = lang or _get_lang(frame, default_lang)
    if lang and lang != 'en_US':
        return get_translated_module(module or frame), lang
    else:
        # we don't care about the module for 'en_US'
        return module or 'base', 'en_US'