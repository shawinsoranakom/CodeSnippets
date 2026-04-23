def body_encode(body, maxlinelen=76, eol=NL):
    """Encode with quoted-printable, wrapping at maxlinelen characters.

    Each line of encoded text will end with eol, which defaults to "\\n".  Set
    this to "\\r\\n" if you will be using the result of this function directly
    in an email.

    Each line will be wrapped at, at most, maxlinelen characters before the
    eol string (maxlinelen defaults to 76 characters, the maximum value
    permitted by RFC 2045).  Long lines will have the 'soft line break'
    quoted-printable character "=" appended to them, so the decoded text will
    be identical to the original text.

    The minimum maxlinelen is 4 to have room for a quoted character ("=XX")
    followed by a soft line break.  Smaller values will generate a
    ValueError.

    """

    if maxlinelen < 4:
        raise ValueError("maxlinelen must be at least 4")
    if not body:
        return body

    # quote special characters
    body = body.translate(_QUOPRI_BODY_ENCODE_MAP)

    soft_break = '=' + eol
    # leave space for the '=' at the end of a line
    maxlinelen1 = maxlinelen - 1

    encoded_body = []
    append = encoded_body.append

    for line in body.splitlines():
        # break up the line into pieces no longer than maxlinelen - 1
        start = 0
        laststart = len(line) - 1 - maxlinelen
        while start <= laststart:
            stop = start + maxlinelen1
            # make sure we don't break up an escape sequence
            if line[stop - 2] == '=':
                append(line[start:stop - 1])
                start = stop - 2
            elif line[stop - 1] == '=':
                append(line[start:stop])
                start = stop - 1
            else:
                append(line[start:stop] + '=')
                start = stop

        # handle rest of line, special case if line ends in whitespace
        if line and line[-1] in ' \t':
            room = start - laststart
            if room >= 3:
                # It's a whitespace character at end-of-line, and we have room
                # for the three-character quoted encoding.
                q = quote(line[-1])
            elif room == 2:
                # There's room for the whitespace character and a soft break.
                q = line[-1] + soft_break
            else:
                # There's room only for a soft break.  The quoted whitespace
                # will be the only content on the subsequent line.
                q = soft_break + quote(line[-1])
            append(line[start:-1] + q)
        else:
            append(line[start:])

    # add back final newline if present
    if body[-1] in CRLF:
        append('')

    return eol.join(encoded_body)