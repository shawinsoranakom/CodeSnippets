def get_encoded_word(value, terminal_type='vtext'):
    """ encoded-word = "=?" charset "?" encoding "?" encoded-text "?="

    """
    ew = EncodedWord()
    if not value.startswith('=?'):
        raise errors.HeaderParseError(
            "expected encoded word but found {}".format(value))
    tok, *remainder = value[2:].split('?=', 1)
    if tok == value[2:]:
        raise errors.HeaderParseError(
            "expected encoded word but found {}".format(value))
    remstr = ''.join(remainder)
    if (len(remstr) > 1 and
        remstr[0] in hexdigits and
        remstr[1] in hexdigits and
        tok.count('?') < 2):
        # The ? after the CTE was followed by an encoded word escape (=XX).
        rest, *remainder = remstr.split('?=', 1)
        tok = tok + '?=' + rest
    if len(tok.split()) > 1:
        ew.defects.append(errors.InvalidHeaderDefect(
            "whitespace inside encoded word"))
    ew.cte = value
    value = ''.join(remainder)
    try:
        text, charset, lang, defects = _ew.decode('=?' + tok + '?=')
    except (ValueError, KeyError):
        raise _InvalidEwError(
            "encoded word format invalid: '{}'".format(ew.cte))
    ew.charset = charset
    ew.lang = lang
    ew.defects.extend(defects)
    while text:
        if text[0] in WSP:
            token, text = get_fws(text)
            ew.append(token)
            continue
        chars, *remainder = _wsp_splitter(text, 1)
        vtext = ValueTerminal(chars, terminal_type)
        _validate_xtext(vtext)
        ew.append(vtext)
        text = ''.join(remainder)
    # Encoded words should be followed by a WS
    if value and value[0] not in WSP:
        ew.defects.append(errors.InvalidHeaderDefect(
            "missing trailing whitespace after encoded-word"))
    return ew, value