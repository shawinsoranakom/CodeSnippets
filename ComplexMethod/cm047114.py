def url_join(
    base: str | tuple[str, str, str, str, str],
    url: str | tuple[str, str, str, str, str],
    allow_fragments: bool = True,
) -> str:
    """Join a base URL and a possibly relative URL to form an absolute
    interpretation of the latter.

    :param base: the base URL for the join operation.
    :param url: the URL to join.
    :param allow_fragments: indicates whether fragments should be allowed.

    .. deprecated:: 2.3
        Will be removed in Werkzeug 2.4. Use ``urllib.parse.urljoin`` instead.
    """
    if isinstance(base, tuple):
        base = url_unparse(base)
    if isinstance(url, tuple):
        url = url_unparse(url)

    _check_str_tuple((base, url))
    s = _make_encode_wrapper(base)

    if not base:
        return url
    if not url:
        return base

    bscheme, bnetloc, bpath, bquery, _bfragment = url_parse(
        base, allow_fragments=allow_fragments
    )
    scheme, netloc, path, query, fragment = url_parse(url, bscheme, allow_fragments)
    if scheme != bscheme:
        return url
    if netloc:
        return url_unparse((scheme, netloc, path, query, fragment))
    netloc = bnetloc

    if path[:1] == s("/"):
        segments = path.split(s("/"))
    elif not path:
        segments = bpath.split(s("/"))
        if not query:
            query = bquery
    else:
        segments = bpath.split(s("/"))[:-1] + path.split(s("/"))

    # If the rightmost part is "./" we want to keep the slash but
    # remove the dot.
    if segments[-1] == s("."):
        segments[-1] = s("")

    # Resolve ".." and "."
    segments = [segment for segment in segments if segment != s(".")]
    while True:
        i = 1
        n = len(segments) - 1
        while i < n:
            if segments[i] == s("..") and segments[i - 1] not in (s(""), s("..")):
                del segments[i - 1 : i + 1]
                break
            i += 1
        else:
            break

    # Remove trailing ".." if the URL is absolute
    unwanted_marker = [s(""), s("..")]
    while segments[:2] == unwanted_marker:
        del segments[1]

    path = s("/").join(segments)
    return url_unparse((scheme, netloc, path, query, fragment))