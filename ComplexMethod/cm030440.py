def get_section(value):
    """ '*' digits

    The formal BNF is more complicated because leading 0s are not allowed.  We
    check for that and add a defect.  We also assume no CFWS is allowed between
    the '*' and the digits, though the RFC is not crystal clear on that.
    The caller should already have dealt with leading CFWS.

    """
    section = Section()
    if not value or value[0] != '*':
        raise errors.HeaderParseError("Expected section but found {}".format(
                                        value))
    section.append(ValueTerminal('*', 'section-marker'))
    value = value[1:]
    if not value or not value[0].isdigit():
        raise errors.HeaderParseError("Expected section number but "
                                      "found {}".format(value))
    digits = ''
    while value and value[0].isdigit():
        digits += value[0]
        value = value[1:]
    if digits[0] == '0' and digits != '0':
        section.defects.append(errors.InvalidHeaderDefect(
                "section number has an invalid leading 0"))
    section.number = int(digits)
    section.append(ValueTerminal(digits, 'digits'))
    return section, value