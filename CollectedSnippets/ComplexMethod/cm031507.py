def _parse_sequence(sequence):
    """Get a string which should describe an event sequence. If it is
    successfully parsed as one, return a tuple containing the state (as an int),
    the event type (as an index of _types), and the detail - None if none, or a
    string if there is one. If the parsing is unsuccessful, return None.
    """
    if not sequence or sequence[0] != '<' or sequence[-1] != '>':
        return None
    words = sequence[1:-1].split('-')
    modifiers = 0
    while words and words[0] in _modifier_names:
        modifiers |= 1 << _modifier_names[words[0]]
        del words[0]
    if words and words[0] in _type_names:
        type = _type_names[words[0]]
        del words[0]
    else:
        return None
    if _binder_classes[type] is _SimpleBinder:
        if modifiers or words:
            return None
        else:
            detail = None
    else:
        # _ComplexBinder
        if type in [_type_names[s] for s in ("KeyPress", "KeyRelease")]:
            type_re = _keysym_re
        else:
            type_re = _button_re

        if not words:
            detail = None
        elif len(words) == 1 and type_re.match(words[0]):
            detail = words[0]
        else:
            return None

    return modifiers, type, detail