def url_unparse(components: tuple[str, str, str, str, str]) -> str:
    """The reverse operation to :meth:`url_parse`.  This accepts arbitrary
    as well as :class:`URL` tuples and returns a URL as a string.

    :param components: the parsed URL as tuple which should be converted
                       into a URL string.

    .. deprecated:: 2.3
        Will be removed in Werkzeug 2.4. Use ``urllib.parse.urlunsplit`` instead.
    """

    _check_str_tuple(components)
    scheme, netloc, path, query, fragment = components
    s = _make_encode_wrapper(scheme)
    url = s("")

    # We generally treat file:///x and file:/x the same which is also
    # what browsers seem to do.  This also allows us to ignore a schema
    # register for netloc utilization or having to differentiate between
    # empty and missing netloc.
    if netloc or (scheme and path.startswith(s("/"))):
        if path and path[:1] != s("/"):
            path = s("/") + path
        url = s("//") + (netloc or s("")) + path
    elif path:
        url += path
    if scheme:
        url = scheme + s(":") + url
    if query:
        url = url + s("?") + query
    if fragment:
        url = url + s("#") + fragment
    return url