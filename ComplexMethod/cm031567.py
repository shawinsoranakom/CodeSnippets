def _urlsplit(url, scheme=None, allow_fragments=True):
    # Only lstrip url as some applications rely on preserving trailing space.
    # (https://url.spec.whatwg.org/#concept-basic-url-parser would strip both)
    url = url.lstrip(_WHATWG_C0_CONTROL_OR_SPACE)
    for b in _UNSAFE_URL_BYTES_TO_REMOVE:
        url = url.replace(b, "")
    if scheme is not None:
        scheme = scheme.strip(_WHATWG_C0_CONTROL_OR_SPACE)
        for b in _UNSAFE_URL_BYTES_TO_REMOVE:
            scheme = scheme.replace(b, "")

    allow_fragments = bool(allow_fragments)
    netloc = query = fragment = None
    i = url.find(':')
    if i > 0 and url[0].isascii() and url[0].isalpha():
        for c in url[:i]:
            if c not in scheme_chars:
                break
        else:
            scheme, url = url[:i].lower(), url[i+1:]
    if url[:2] == '//':
        netloc, url = _splitnetloc(url, 2)
        if (('[' in netloc and ']' not in netloc) or
                (']' in netloc and '[' not in netloc)):
            raise ValueError("Invalid IPv6 URL")
        if '[' in netloc and ']' in netloc:
            _check_bracketed_netloc(netloc)
    if allow_fragments and '#' in url:
        url, fragment = url.split('#', 1)
    if '?' in url:
        url, query = url.split('?', 1)
    _checknetloc(netloc)
    return (scheme, netloc, url, query, fragment)