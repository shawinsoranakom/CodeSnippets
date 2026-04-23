def get_name_addr(value):
    """ name-addr = [display-name] angle-addr

    """
    name_addr = NameAddr()
    # Both the optional display name and the angle-addr can start with cfws.
    leader = None
    if not value:
        raise errors.HeaderParseError(
            "expected name-addr but found '{}'".format(value))
    if value[0] in CFWS_LEADER:
        leader, value = get_cfws(value)
        if not value:
            raise errors.HeaderParseError(
                "expected name-addr but found '{}'".format(leader))
    if value[0] != '<':
        if value[0] in PHRASE_ENDS:
            raise errors.HeaderParseError(
                "expected name-addr but found '{}'".format(value))
        token, value = get_display_name(value)
        if not value:
            raise errors.HeaderParseError(
                "expected name-addr but found '{}'".format(token))
        if leader is not None:
            if isinstance(token[0], TokenList):
                token[0][:0] = [leader]
            else:
                token[:0] = [leader]
            leader = None
        name_addr.append(token)
    token, value = get_angle_addr(value)
    if leader is not None:
        token[:0] = [leader]
    name_addr.append(token)
    return name_addr, value