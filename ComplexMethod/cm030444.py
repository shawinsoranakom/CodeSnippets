def _refold_parse_tree(parse_tree, *, policy):
    """Return string of contents of parse_tree folded according to RFC rules.

    """
    # max_line_length 0/None means no limit, ie: infinitely long.
    maxlen = policy.max_line_length or sys.maxsize
    encoding = 'utf-8' if policy.utf8 else 'us-ascii'
    lines = ['']  # Folded lines to be output
    last_word_is_ew = False
    last_ew = None  # if there is an encoded word in the last line of lines,
                    # points to the encoded word's first character
    last_charset = None
    wrap_as_ew_blocked = 0
    want_encoding = False  # This is set to True if we need to encode this part
    end_ew_not_allowed = Terminal('', 'wrap_as_ew_blocked')
    parts = list(parse_tree)
    while parts:
        part = parts.pop(0)
        if part is end_ew_not_allowed:
            wrap_as_ew_blocked -= 1
            continue
        tstr = str(part)
        if not want_encoding:
            if part.token_type in ('ptext', 'vtext'):
                # Encode if tstr contains special characters.
                want_encoding = not SPECIALSNL.isdisjoint(tstr)
            else:
                # Encode if tstr contains newlines.
                want_encoding = not NLSET.isdisjoint(tstr)
        try:
            tstr.encode(encoding)
            charset = encoding
        except UnicodeEncodeError:
            if any(isinstance(x, errors.UndecodableBytesDefect)
                   for x in part.all_defects):
                charset = 'unknown-8bit'
            else:
                # If policy.utf8 is false this should really be taken from a
                # 'charset' property on the policy.
                charset = 'utf-8'
            want_encoding = True

        if part.token_type == 'mime-parameters':
            # Mime parameter folding (using RFC2231) is extra special.
            _fold_mime_parameters(part, lines, maxlen, encoding)
            last_word_is_ew = False
            continue

        if want_encoding and not wrap_as_ew_blocked:
            if not part.as_ew_allowed:
                want_encoding = False
                last_ew = None
                if part.syntactic_break:
                    encoded_part = part.fold(policy=policy)[:-len(policy.linesep)]
                    if policy.linesep not in encoded_part:
                        # It fits on a single line
                        if len(encoded_part) > maxlen - len(lines[-1]):
                            # But not on this one, so start a new one.
                            newline = _steal_trailing_WSP_if_exists(lines)
                            # XXX what if encoded_part has no leading FWS?
                            lines.append(newline)
                        lines[-1] += encoded_part
                        last_word_is_ew = False
                        continue
                # Either this is not a major syntactic break, so we don't
                # want it on a line by itself even if it fits, or it
                # doesn't fit on a line by itself.  Either way, fall through
                # to unpacking the subparts and wrapping them.
            if not hasattr(part, 'encode'):
                # It's not a Terminal, do each piece individually.
                parts = list(part) + parts
                want_encoding = False
                continue
            elif part.as_ew_allowed:
                # It's a terminal, wrap it as an encoded word, possibly
                # combining it with previously encoded words if allowed.
                if (last_ew is not None and
                    charset != last_charset and
                    (last_charset == 'unknown-8bit' or
                     last_charset == 'utf-8' and charset != 'us-ascii')):
                    last_ew = None
                last_ew = _fold_as_ew(
                    tstr,
                    lines,
                    maxlen,
                    last_ew,
                    part.ew_combine_allowed,
                    charset,
                    last_word_is_ew,
                )
                last_word_is_ew = True
                last_charset = charset
                want_encoding = False
                continue
            else:
                # It's a terminal which should be kept non-encoded
                # (e.g. a ListSeparator).
                last_ew = None
                want_encoding = False
                # fall through

        if len(tstr) <= maxlen - len(lines[-1]):
            lines[-1] += tstr
            last_word_is_ew = last_word_is_ew and not bool(tstr.strip(_WSP))
            continue

        # This part is too long to fit.  The RFC wants us to break at
        # "major syntactic breaks", so unless we don't consider this
        # to be one, check if it will fit on the next line by itself.
        if (part.syntactic_break and
                len(tstr) + 1 <= maxlen):
            newline = _steal_trailing_WSP_if_exists(lines)
            if newline or part.startswith_fws():
                lines.append(newline + tstr)
                last_word_is_ew = (last_word_is_ew
                                   and not bool(lines[-1].strip(_WSP)))
                last_ew = None
                continue
        if not hasattr(part, 'encode'):
            # It's not a terminal, try folding the subparts.
            newparts = list(part)
            if part.token_type == 'bare-quoted-string':
                # To fold a quoted string we need to create a list of terminal
                # tokens that will render the leading and trailing quotes
                # and use quoted pairs in the value as appropriate.
                newparts = (
                    [ValueTerminal('"', 'ptext')] +
                    [ValueTerminal(make_quoted_pairs(p), 'ptext')
                     for p in newparts] +
                    [ValueTerminal('"', 'ptext')])
            if part.token_type == 'comment':
                newparts = (
                    [ValueTerminal('(', 'ptext')] +
                    [ValueTerminal(make_parenthesis_pairs(p), 'ptext')
                     if p.token_type == 'ptext' else p
                     for p in newparts] +
                    [ValueTerminal(')', 'ptext')])
            if not part.as_ew_allowed:
                wrap_as_ew_blocked += 1
                newparts.append(end_ew_not_allowed)
            parts = newparts + parts
            continue
        if part.as_ew_allowed and not wrap_as_ew_blocked:
            # It doesn't need CTE encoding, but encode it anyway so we can
            # wrap it.
            parts.insert(0, part)
            want_encoding = True
            continue
        # We can't figure out how to wrap, it, so give up.
        newline = _steal_trailing_WSP_if_exists(lines)
        if newline or part.startswith_fws():
            lines.append(newline + tstr)
        else:
            # We can't fold it onto the next line either...
            lines[-1] += tstr
        last_word_is_ew = last_word_is_ew and not bool(tstr.strip(_WSP))

    return policy.linesep.join(lines) + policy.linesep