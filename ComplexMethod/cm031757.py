def parse_spec(spec):
    """Parse a keyword spec string into a dictionary.

    The keyword spec format defines the name of the gettext function and the
    positions of the arguments that correspond to msgid, msgid_plural, and
    msgctxt. The format is as follows:

        name - the name of the gettext function, assumed to
               have a single argument that is the msgid.
        name:pos1 - the name of the gettext function and the position
                    of the msgid argument.
        name:pos1,pos2 - the name of the gettext function and the positions
                         of the msgid and msgid_plural arguments.
        name:pos1,pos2c - the name of the gettext function and the positions
                          of the msgid and msgctxt arguments.
        name:pos1,pos2,pos3c - the name of the gettext function and the
                               positions of the msgid, msgid_plural, and
                               msgctxt arguments.

    As an example, the spec 'foo:1,2,3c' means that the function foo has three
    arguments, the first one is the msgid, the second one is the msgid_plural,
    and the third one is the msgctxt. The positions are 1-based.

    The msgctxt argument can appear in any position, but it can only appear
    once. For example, the keyword specs 'foo:3c,1,2' and 'foo:1,2,3c' are
    equivalent.

    See https://www.gnu.org/software/gettext/manual/gettext.html
    for more information.
    """
    parts = spec.strip().split(':', 1)
    if len(parts) == 1:
        name = parts[0]
        return name, {'msgid': 0}

    name, args = parts
    if not args:
        raise ValueError(f'Invalid keyword spec {spec!r}: '
                         'missing argument positions')

    result = {}
    for arg in args.split(','):
        arg = arg.strip()
        is_context = False
        if arg.endswith('c'):
            is_context = True
            arg = arg[:-1]

        try:
            pos = int(arg) - 1
        except ValueError as e:
            raise ValueError(f'Invalid keyword spec {spec!r}: '
                             'position is not an integer') from e

        if pos < 0:
            raise ValueError(f'Invalid keyword spec {spec!r}: '
                             'argument positions must be strictly positive')

        if pos in result.values():
            raise ValueError(f'Invalid keyword spec {spec!r}: '
                             'duplicate positions')

        if is_context:
            if 'msgctxt' in result:
                raise ValueError(f'Invalid keyword spec {spec!r}: '
                                 'msgctxt can only appear once')
            result['msgctxt'] = pos
        elif 'msgid' not in result:
            result['msgid'] = pos
        elif 'msgid_plural' not in result:
            result['msgid_plural'] = pos
        else:
            raise ValueError(f'Invalid keyword spec {spec!r}: '
                             'too many positions')

    if 'msgid' not in result and 'msgctxt' in result:
        raise ValueError(f'Invalid keyword spec {spec!r}: '
                         'msgctxt cannot appear without msgid')

    return name, result