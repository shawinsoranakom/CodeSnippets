def _(self, source: str | LazyGettext, *args, **kwargs) -> str:
        """Translate the term using current environment's language.

        Usage:

        ```
        self.env._("hello world")  # dynamically get module name
        self.env._("hello %s", "test")
        self.env._(LAZY_TRANSLATION)
        ```

        :param source: String to translate or lazy translation
        :param ...: args or kwargs for templating
        :return: The transalted string
        """
        lang = self.lang or 'en_US'
        if isinstance(source, str):
            assert not (args and kwargs), "Use args or kwargs, not both"
            format_args = args or kwargs
        elif isinstance(source, LazyGettext):
            # translate a lazy text evaluation
            assert not args and not kwargs, "All args should come from the lazy text"
            return source._translate(lang)
        else:
            raise TypeError(f"Cannot translate {source!r}")
        if lang == 'en_US':
            # we ignore the module as en_US is not translated
            return get_translation('base', 'en_US', source, format_args)
        try:
            module = get_translated_module(2)
            return get_translation(module, lang, source, format_args)
        except Exception:  # noqa: BLE001
            _logger.debug('translation went wrong for "%r", skipped', source, exc_info=True)
        return source