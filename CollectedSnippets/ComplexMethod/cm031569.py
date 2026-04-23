def urlunsplit(components, *, keep_empty=_UNSPECIFIED):
    """Combine the elements of a tuple as returned by urlsplit() into a
    complete URL as a string. The data argument can be any five-item iterable.
    This may result in a slightly different, but equivalent URL, if the URL that
    was parsed originally had unnecessary delimiters (for example, a ? with an
    empty query; the RFC states that these are equivalent) and keep_empty
    is false or components is the result of the urlsplit() call with
    missing_as_none=False."""
    scheme, netloc, url, query, fragment, _coerce_result = (
                                          _coerce_args(*components))
    if keep_empty is _UNSPECIFIED:
        keep_empty = getattr(components, '_keep_empty', _MISSING_AS_NONE_DEFAULT)
    elif keep_empty and not getattr(components, '_keep_empty', True):
        raise ValueError('Cannot distinguish between empty and not defined '
                         'URI components in the result of parsing URL with '
                         'missing_as_none=False')
    if not keep_empty:
        if not netloc:
            if scheme and scheme in uses_netloc and (not url or url[:1] == '/'):
                netloc = ''
            else:
                netloc = None
        if not scheme: scheme = None
        if not query: query = None
        if not fragment: fragment = None
    return _coerce_result(_urlunsplit(scheme, netloc, url, query, fragment))