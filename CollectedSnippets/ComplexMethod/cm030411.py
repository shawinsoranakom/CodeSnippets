def decode_params(params):
    """Decode parameters list according to RFC 2231.

    params is a sequence of 2-tuples containing (param name, string value).
    """
    new_params = [params[0]]
    # Map parameter's name to a list of continuations.  The values are a
    # 3-tuple of the continuation number, the string value, and a flag
    # specifying whether a particular segment is %-encoded.
    rfc2231_params = {}
    for name, value in params[1:]:
        encoded = name.endswith('*')
        value = unquote(value)
        mo = rfc2231_continuation.match(name)
        if mo:
            name, num = mo.group('name', 'num')
            if num is not None:
                num = int(num)
            rfc2231_params.setdefault(name, []).append((num, value, encoded))
        else:
            new_params.append((name, '"%s"' % quote(value)))
    if rfc2231_params:
        for name, continuations in rfc2231_params.items():
            value = []
            extended = False
            # Sort by number, treating None as 0 if there is no 0,
            # and ignore it if there is already a 0.
            has_zero = any(x[0] == 0 for x in continuations)
            if has_zero:
                continuations = [x for x in continuations if x[0] is not None]
            else:
                continuations = [(x[0] or 0, x[1], x[2]) for x in continuations]
            continuations.sort(key=lambda x: x[0])
            # And now append all values in numerical order, converting
            # %-encodings for the encoded segments.  If any of the
            # continuation names ends in a *, then the entire string, after
            # decoding segments and concatenating, must have the charset and
            # language specifiers at the beginning of the string.
            for num, s, encoded in continuations:
                if encoded:
                    # Decode as "latin-1", so the characters in s directly
                    # represent the percent-encoded octet values.
                    # collapse_rfc2231_value treats this as an octet sequence.
                    s = urllib.parse.unquote(s, encoding="latin-1")
                    extended = True
                value.append(s)
            value = quote(EMPTYSTRING.join(value))
            if extended:
                charset, language, value = decode_rfc2231(value)
                new_params.append((name, (charset, language, '"%s"' % value)))
            else:
                new_params.append((name, '"%s"' % value))
    return new_params