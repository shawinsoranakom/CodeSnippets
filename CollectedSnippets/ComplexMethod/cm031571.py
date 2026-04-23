def urljoin(base, url, allow_fragments=True):
    """Join a base URL and a possibly relative URL to form an absolute
    interpretation of the latter."""
    if not base:
        return url
    if not url:
        return base

    base, url, _coerce_result = _coerce_args(base, url)
    bscheme, bnetloc, bpath, bquery, bfragment = \
            _urlsplit(base, None, allow_fragments)
    scheme, netloc, path, query, fragment = \
            _urlsplit(url, None, allow_fragments)

    if scheme is None:
        scheme = bscheme
    if scheme != bscheme or (scheme and scheme not in uses_relative):
        return _coerce_result(url)
    if not scheme or scheme in uses_netloc:
        if netloc:
            return _coerce_result(_urlunsplit(scheme, netloc, path,
                                              query, fragment))
        netloc = bnetloc

    if not path:
        path = bpath
        if query is None:
            query = bquery
            if fragment is None:
                fragment = bfragment
        return _coerce_result(_urlunsplit(scheme, netloc, path,
                                          query, fragment))

    base_parts = bpath.split('/')
    if base_parts[-1] != '':
        # the last item is not a directory, so will not be taken into account
        # in resolving the relative path
        del base_parts[-1]

    # for rfc3986, ignore all base path should the first character be root.
    if path[:1] == '/':
        segments = path.split('/')
    else:
        segments = base_parts + path.split('/')
        # filter out elements that would cause redundant slashes on re-joining
        # the resolved_path
        segments[1:-1] = filter(None, segments[1:-1])

    resolved_path = []

    for seg in segments:
        if seg == '..':
            try:
                resolved_path.pop()
            except IndexError:
                # ignore any .. segments that would otherwise cause an IndexError
                # when popped from resolved_path if resolving for rfc3986
                pass
        elif seg == '.':
            continue
        else:
            resolved_path.append(seg)

    if segments[-1] in ('.', '..'):
        # do some post-processing here. if the last segment was a relative dir,
        # then we need to append the trailing '/'
        resolved_path.append('')

    return _coerce_result(_urlunsplit(scheme, netloc, '/'.join(
        resolved_path) or '/', query, fragment))