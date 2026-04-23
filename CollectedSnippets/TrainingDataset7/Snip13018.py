def __init__(self, get_response, cache_timeout=None, page_timeout=None, **kwargs):
        super().__init__(get_response)
        # We need to differentiate between "provided, but using default value",
        # and "not provided". If the value is provided using a default, then
        # we fall back to system defaults. If it is not provided at all,
        # we need to use middleware defaults.

        try:
            key_prefix = kwargs["key_prefix"]
            if key_prefix is None:
                key_prefix = ""
            self.key_prefix = key_prefix
        except KeyError:
            pass
        try:
            cache_alias = kwargs["cache_alias"]
            if cache_alias is None:
                cache_alias = DEFAULT_CACHE_ALIAS
            self.cache_alias = cache_alias
        except KeyError:
            pass

        if cache_timeout is not None:
            self.cache_timeout = cache_timeout
        self.page_timeout = page_timeout