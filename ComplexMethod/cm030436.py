def get_group(value):
    """ group = display-name ":" [group-list] ";" [CFWS]

    """
    group = Group()
    token, value = get_display_name(value)
    if not value or value[0] != ':':
        raise errors.HeaderParseError("expected ':' at end of group "
            "display name but found '{}'".format(value))
    group.append(token)
    group.append(ValueTerminal(':', 'group-display-name-terminator'))
    value = value[1:]
    if value and value[0] == ';':
        group.append(ValueTerminal(';', 'group-terminator'))
        return group, value[1:]
    token, value = get_group_list(value)
    group.append(token)
    if not value:
        group.defects.append(errors.InvalidHeaderDefect(
            "end of header in group"))
    elif value[0] != ';':
        raise errors.HeaderParseError(
            "expected ';' at end of group but found {}".format(value))
    group.append(ValueTerminal(';', 'group-terminator'))
    value = value[1:]
    if value and value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        group.append(token)
    return group, value