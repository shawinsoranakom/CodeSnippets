def _build_repr(self):
    init = self.__class__.__init__
    # Ignore varargs, kw and default values and pop self
    init_signature = signature(init)
    # Consider the constructor parameters excluding 'self'
    if init is object.__init__:
        args = []
    else:
        args = sorted(
            [
                p.name
                for p in init_signature.parameters.values()
                if p.name != "self" and p.kind != p.VAR_KEYWORD
            ]
        )
    class_name = self.__class__.__name__
    params = dict()
    for key in args:
        with warnings.catch_warnings(record=True) as w:
            # We need deprecation warnings to always be on in order to
            # catch deprecated param values.
            # This is set in utils/__init__.py but it gets overwritten
            # when running under python3 somehow.
            warnings.simplefilter("always", FutureWarning)
            value = getattr(self, key, None)
            if value is None and hasattr(self, "cvargs"):
                value = self.cvargs.get(key, None)
        if len(w) and w[0].category is FutureWarning:
            # if the parameter is deprecated, don't show it
            continue

        params[key] = value

    return "%s(%s)" % (class_name, _pprint(params, offset=len(class_name)))