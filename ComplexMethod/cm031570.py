def _urlunsplit(scheme, netloc, url, query, fragment):
    if netloc is not None:
        if url and url[:1] != '/': url = '/' + url
        url = '//' + netloc + url
    elif url[:2] == '//':
        url = '//' + url
    if scheme:
        url = scheme + ':' + url
    if query is not None:
        url = url + '?' + query
    if fragment is not None:
        url = url + '#' + fragment
    return url