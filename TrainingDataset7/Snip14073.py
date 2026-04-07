def __get__(self, instance, cls=None):
        """
        Return a compiled regular expression based on the active language.
        """
        if instance is None:
            return self
        # As a performance optimization, if the given route is a regular string
        # (not a lazily-translated string proxy), compile it once and avoid
        # per-language compilation.
        if isinstance(instance._route, str):
            instance.__dict__["regex"] = re.compile(instance._regex)
            return instance.__dict__["regex"]
        language_code = get_language()
        if language_code not in instance._regex_dict:
            instance._regex_dict[language_code] = re.compile(
                _route_to_regex(str(instance._route), instance._is_endpoint)[0]
            )
        return instance._regex_dict[language_code]