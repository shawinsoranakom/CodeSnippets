def smart_urlquote(url):
    """Quote a URL if it isn't already quoted."""

    def unquote_quote(segment):
        segment = unquote(segment)
        # Tilde is part of RFC 3986 Section 2.3 Unreserved Characters,
        # see also https://bugs.python.org/issue16285
        return quote(segment, safe=RFC3986_SUBDELIMS + RFC3986_GENDELIMS + "~")

    try:
        scheme, netloc, path, query, fragment = urlsplit(url)
    except ValueError:
        # invalid IPv6 URL (normally square brackets in hostname part).
        return unquote_quote(url)

    # Handle IDN as percent-encoded UTF-8 octets, per WHATWG URL Specification
    # section 3.5 and RFC 3986 section 3.2.2. Defer any IDNA to the user agent.
    # See #36013.
    netloc = unquote_quote(netloc)

    if query:
        # Separately unquoting key/value, so as to not mix querystring
        # separators included in query values. See #22267.
        query_parts = [
            (unquote(q[0]), unquote(q[1]))
            for q in parse_qsl(query, keep_blank_values=True)
        ]
        # urlencode will take care of quoting
        query = urlencode(query_parts)

    path = unquote_quote(path)
    fragment = unquote_quote(fragment)

    return urlunsplit((scheme, netloc, path, query, fragment))