def unquote_quote(segment):
        segment = unquote(segment)
        # Tilde is part of RFC 3986 Section 2.3 Unreserved Characters,
        # see also https://bugs.python.org/issue16285
        return quote(segment, safe=RFC3986_SUBDELIMS + RFC3986_GENDELIMS + "~")