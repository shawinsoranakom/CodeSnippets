def get_translation(module: str, lang: str, source: str, args: tuple | dict) -> str:
    """Translate and format using a module, language, source text and args."""
    # get the translation by using the language
    assert lang, "missing language for translation"
    if lang == 'en_US':
        translation = source
    else:
        assert module, "missing module name for translation"
        translation = code_translations.get_python_translations(module, lang).get(source, source)
    # skip formatting if we have no args
    if not args:
        return translation
    # we need to check the args for markup values and for lazy translations
    args_is_dict = isinstance(args, dict)
    if any(isinstance(a, Markup) for a in (args.values() if args_is_dict else args)):
        translation = escape(translation)
    if any(isinstance(a, LazyGettext) for a in (args.values() if args_is_dict else args)):
        if args_is_dict:
            args = {k: v._translate(lang) if isinstance(v, LazyGettext) else v for k, v in args.items()}
        else:
            args = tuple(v._translate(lang) if isinstance(v, LazyGettext) else v for v in args)
    if any(isinstance(a, Iterable) and not isinstance(a, (str, bytes)) for a in (args.values() if args_is_dict else args)):
        # automatically format list-like arguments in a localized way
        def process_translation_arg(v):
            return format_list(env=None, lst=v, lang_code=lang) if isinstance(v, Iterable) and not isinstance(v, (str, bytes)) else v
        if args_is_dict:
            args = {k: process_translation_arg(v) for k, v in args.items()}
        else:
            args = tuple(process_translation_arg(v) for v in args)
    # format
    try:
        return translation % args
    except (TypeError, ValueError, KeyError):
        bad = translation
        # fallback: apply to source before logging exception (in case source fails)
        translation = source % args
        _logger.exception('Bad translation %r for string %r', bad, source)
    return translation