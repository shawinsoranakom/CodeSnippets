def urlparse(url, scheme=None, allow_fragments=True, *, missing_as_none=_MISSING_AS_NONE_DEFAULT):
    """Parse a URL into 6 components:
    <scheme>://<netloc>/<path>;<params>?<query>#<fragment>

    The result is a named 6-tuple with fields corresponding to the
    above. It is either a ParseResult or ParseResultBytes object,
    depending on the type of the url parameter.

    The username, password, hostname, and port sub-components of netloc
    can also be accessed as attributes of the returned object.

    The scheme argument provides the default value of the scheme
    component when no scheme is found in url.

    If allow_fragments is False, no attempt is made to separate the
    fragment component from the previous component, which can be either
    path or query.

    Note that % escapes are not expanded.

    urlsplit() should generally be used instead of urlparse().
    """
    url, scheme, _coerce_result = _coerce_args(url, scheme)
    if url is None:
        url = ''
    scheme, netloc, url, params, query, fragment = _urlparse(url, scheme, allow_fragments)
    if not missing_as_none:
        if scheme is None: scheme = ''
        if netloc is None: netloc = ''
        if params is None: params = ''
        if query is None: query = ''
        if fragment is None: fragment = ''
    result = ParseResult(scheme, netloc, url, params, query, fragment)
    result = _coerce_result(result)
    result._keep_empty = missing_as_none
    return result