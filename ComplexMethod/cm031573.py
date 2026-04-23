def parse_qsl(qs, keep_blank_values=False, strict_parsing=False,
              encoding='utf-8', errors='replace', max_num_fields=None, separator='&', *, _stacklevel=1):
    """Parse a query given as a string argument.

        Arguments:

        qs: percent-encoded query string to be parsed

        keep_blank_values: flag indicating whether blank values in
            percent-encoded queries should be treated as blank strings.
            A true value indicates that blanks should be retained as blank
            strings.  The default false value indicates that blank values
            are to be ignored and treated as if they were  not included.

        strict_parsing: flag indicating what to do with parsing errors. If
            false (the default), errors are silently ignored. If true,
            errors raise a ValueError exception.

        encoding and errors: specify how to decode percent-encoded sequences
            into Unicode characters, as accepted by the bytes.decode() method.

        max_num_fields: int. If set, then throws a ValueError
            if there are more than n fields read by parse_qsl().

        separator: str. The symbol to use for separating the query arguments.
            Defaults to &.

        Returns a list, as G-d intended.
    """
    if not separator or not isinstance(separator, (str, bytes)):
        raise ValueError("Separator must be of type string or bytes.")
    if isinstance(qs, str):
        if not isinstance(separator, str):
            separator = str(separator, 'ascii')
        eq = '='
        def _unquote(s):
            return unquote_plus(s, encoding=encoding, errors=errors)
    elif qs is None:
        return []
    else:
        try:
            # Use memoryview() to reject integers and iterables,
            # acceptable by the bytes constructor.
            qs = bytes(memoryview(qs))
        except TypeError:
            if not qs:
                warnings.warn(f"Accepting {type(qs).__name__} objects with "
                              f"false value in urllib.parse.parse_qsl() is "
                              f"deprecated as of 3.14",
                              DeprecationWarning, stacklevel=_stacklevel + 1)
                return []
            raise
        if isinstance(separator, str):
            separator = bytes(separator, 'ascii')
        eq = b'='
        def _unquote(s):
            return unquote_to_bytes(s.replace(b'+', b' '))

    if not qs:
        return []

    # If max_num_fields is defined then check that the number of fields
    # is less than max_num_fields. This prevents a memory exhaustion DOS
    # attack via post bodies with many fields.
    if max_num_fields is not None:
        num_fields = 1 + qs.count(separator)
        if max_num_fields < num_fields:
            raise ValueError('Max number of fields exceeded')

    r = []
    for name_value in qs.split(separator):
        if name_value or strict_parsing:
            name, has_eq, value = name_value.partition(eq)
            if not has_eq and strict_parsing:
                raise ValueError("bad query field: %r" % (name_value,))
            if value or keep_blank_values:
                name = _unquote(name)
                value = _unquote(value)
                r.append((name, value))
    return r