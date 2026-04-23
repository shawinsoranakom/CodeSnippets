def get_unstructured(value):
    """unstructured = (*([FWS] vchar) *WSP) / obs-unstruct
       obs-unstruct = *((*LF *CR *(obs-utext) *LF *CR)) / FWS)
       obs-utext = %d0 / obs-NO-WS-CTL / LF / CR

       obs-NO-WS-CTL is control characters except WSP/CR/LF.

    So, basically, we have printable runs, plus control characters or nulls in
    the obsolete syntax, separated by whitespace.  Since RFC 2047 uses the
    obsolete syntax in its specification, but requires whitespace on either
    side of the encoded words, I can see no reason to need to separate the
    non-printable-non-whitespace from the printable runs if they occur, so we
    parse this into xtext tokens separated by WSP tokens.

    Because an 'unstructured' value must by definition constitute the entire
    value, this 'get' routine does not return a remaining value, only the
    parsed TokenList.

    """
    # XXX: but what about bare CR and LF?  They might signal the start or
    # end of an encoded word.  YAGNI for now, since our current parsers
    # will never send us strings with bare CR or LF.

    unstructured = UnstructuredTokenList()
    while value:
        if value[0] in WSP:
            token, value = get_fws(value)
            unstructured.append(token)
            continue
        valid_ew = True
        if value.startswith('=?'):
            try:
                token, value = get_encoded_word(value, 'utext')
            except _InvalidEwError:
                valid_ew = False
            except errors.HeaderParseError:
                # XXX: Need to figure out how to register defects when
                # appropriate here.
                pass
            else:
                have_ws = True
                if len(unstructured) > 0:
                    if unstructured[-1].token_type != 'fws':
                        unstructured.defects.append(errors.InvalidHeaderDefect(
                            "missing whitespace before encoded word"))
                        have_ws = False
                if have_ws and len(unstructured) > 1:
                    if unstructured[-2].token_type == 'encoded-word':
                        unstructured[-1] = EWWhiteSpaceTerminal(
                            unstructured[-1], 'fws')
                unstructured.append(token)
                continue
        tok, *remainder = _wsp_splitter(value, 1)
        # Split in the middle of an atom if there is a rfc2047 encoded word
        # which does not have WSP on both sides. The defect will be registered
        # the next time through the loop.
        # This needs to only be performed when the encoded word is valid;
        # otherwise, performing it on an invalid encoded word can cause
        # the parser to go in an infinite loop.
        if valid_ew and rfc2047_matcher.search(tok):
            tok, *remainder = value.partition('=?')
        vtext = ValueTerminal(tok, 'utext')
        _validate_xtext(vtext)
        unstructured.append(vtext)
        value = ''.join(remainder)
    return unstructured