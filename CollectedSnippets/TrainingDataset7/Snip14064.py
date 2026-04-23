def __get__(self, instance, cls=None):
        """
        Return a compiled regular expression based on the active language.
        """
        if instance is None:
            return self
        # As a performance optimization, if the given regex string is a regular
        # string (not a lazily-translated string proxy), compile it once and
        # avoid per-language compilation.
        pattern = instance._regex
        if isinstance(pattern, str):
            instance.__dict__["regex"] = self._compile(pattern)
            return instance.__dict__["regex"]
        language_code = get_language()
        if language_code not in instance._regex_dict:
            instance._regex_dict[language_code] = self._compile(str(pattern))
        return instance._regex_dict[language_code]