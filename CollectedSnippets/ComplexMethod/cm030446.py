def _fold_mime_parameters(part, lines, maxlen, encoding):
    """Fold TokenList 'part' into the 'lines' list as mime parameters.

    Using the decoded list of parameters and values, format them according to
    the RFC rules, including using RFC2231 encoding if the value cannot be
    expressed in 'encoding' and/or the parameter+value is too long to fit
    within 'maxlen'.

    """
    # Special case for RFC2231 encoding: start from decoded values and use
    # RFC2231 encoding iff needed.
    #
    # Note that the 1 and 2s being added to the length calculations are
    # accounting for the possibly-needed spaces and semicolons we'll be adding.
    #
    for name, value in part.params:
        # XXX What if this ';' puts us over maxlen the first time through the
        # loop?  We should split the header value onto a newline in that case,
        # but to do that we need to recognize the need earlier or reparse the
        # header, so I'm going to ignore that bug for now.  It'll only put us
        # one character over.
        if not lines[-1].rstrip().endswith(';'):
            lines[-1] += ';'
        charset = encoding
        error_handler = 'strict'
        try:
            value.encode(encoding)
            encoding_required = False
        except UnicodeEncodeError:
            encoding_required = True
            if utils._has_surrogates(value):
                charset = 'unknown-8bit'
                error_handler = 'surrogateescape'
            else:
                charset = 'utf-8'
        if encoding_required:
            encoded_value = urllib.parse.quote(
                value, safe='', errors=error_handler)
            tstr = "{}*={}''{}".format(name, charset, encoded_value)
        else:
            tstr = '{}={}'.format(name, quote_string(value))
        if len(lines[-1]) + len(tstr) + 1 < maxlen:
            lines[-1] = lines[-1] + ' ' + tstr
            continue
        elif len(tstr) + 2 <= maxlen:
            lines.append(' ' + tstr)
            continue
        # We need multiple sections.  We are allowed to mix encoded and
        # non-encoded sections, but we aren't going to.  We'll encode them all.
        section = 0
        extra_chrome = charset + "''"
        while value:
            chrome_len = len(name) + len(str(section)) + 3 + len(extra_chrome)
            if maxlen <= chrome_len + 3:
                # We need room for the leading blank, the trailing semicolon,
                # and at least one character of the value.  If we don't
                # have that, we'd be stuck, so in that case fall back to
                # the RFC standard width.
                maxlen = 78
            splitpoint = maxchars = maxlen - chrome_len - 2
            while True:
                partial = value[:splitpoint]
                encoded_value = urllib.parse.quote(
                    partial, safe='', errors=error_handler)
                if len(encoded_value) <= maxchars:
                    break
                splitpoint -= 1
            lines.append(" {}*{}*={}{}".format(
                name, section, extra_chrome, encoded_value))
            extra_chrome = ''
            section += 1
            value = value[splitpoint:]
            if value:
                lines[-1] += ';'