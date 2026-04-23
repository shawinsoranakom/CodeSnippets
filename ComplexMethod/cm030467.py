def decode(encoded, eol=NL):
    """Decode a quoted-printable string.

    Lines are separated with eol, which defaults to \\n.
    """
    if not encoded:
        return encoded
    # BAW: see comment in encode() above.  Again, we're building up the
    # decoded string with string concatenation, which could be done much more
    # efficiently.
    decoded = ''

    for line in encoded.splitlines():
        line = line.rstrip()
        if not line:
            decoded += eol
            continue

        i = 0
        n = len(line)
        while i < n:
            c = line[i]
            if c != '=':
                decoded += c
                i += 1
            # Otherwise, c == "=".  Are we at the end of the line?  If so, add
            # a soft line break.
            elif i+1 == n:
                i += 1
                continue
            # Decode if in form =AB
            elif i+2 < n and line[i+1] in hexdigits and line[i+2] in hexdigits:
                decoded += unquote(line[i:i+3])
                i += 3
            # Otherwise, not in form =AB, pass literally
            else:
                decoded += c
                i += 1

            if i == n:
                decoded += eol
    # Special case if original string did not end with eol
    if encoded[-1] not in '\r\n' and decoded.endswith(eol):
        decoded = decoded[:-len(eol)]
    return decoded