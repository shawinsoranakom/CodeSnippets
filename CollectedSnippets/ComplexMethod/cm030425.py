def get_atom(value):
    """atom = [CFWS] 1*atext [CFWS]

    An atom could be an rfc2047 encoded word.
    """
    atom = Atom()
    if value and value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        atom.append(token)
    if value and value[0] in ATOM_ENDS:
        raise errors.HeaderParseError(
            "expected atom but found '{}'".format(value))
    if value.startswith('=?'):
        try:
            token, value = get_encoded_word(value)
        except errors.HeaderParseError:
            # XXX: need to figure out how to register defects when
            # appropriate here.
            token, value = get_atext(value)
    else:
        token, value = get_atext(value)
    atom.append(token)
    if value and value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        atom.append(token)
    return atom, value