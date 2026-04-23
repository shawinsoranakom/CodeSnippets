def _make_immutable(obj):
    """Recursively convert a container and objects inside of it into immutable data types"""
    if isinstance(obj, (str, bytes)):
        # Strings first because they are also sequences
        return obj
    elif isinstance(obj, Mapping):
        temp_dict = {}
        for key, value in obj.items():
            if isinstance(value, Container):
                temp_dict[key] = _make_immutable(value)
            else:
                temp_dict[key] = value
        return ImmutableDict(temp_dict)
    elif isinstance(obj, Set):
        temp_set = set()
        for value in obj:
            if isinstance(value, Container):
                temp_set.add(_make_immutable(value))
            else:
                temp_set.add(value)
        return frozenset(temp_set)
    elif isinstance(obj, Sequence):
        temp_sequence = []
        for value in obj:
            if isinstance(value, Container):
                temp_sequence.append(_make_immutable(value))
            else:
                temp_sequence.append(value)
        return tuple(temp_sequence)

    return obj