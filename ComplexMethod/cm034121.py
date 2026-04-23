def _sanitize_keys_conditions(value, no_log_strings, ignore_keys, deferred_removals):
    """ Helper method to :func:`sanitize_keys` to build ``deferred_removals`` and avoid deep recursion. """
    if isinstance(value, (str, bytes)):
        return value

    if isinstance(value, Sequence):
        if isinstance(value, MutableSequence):
            new_value = type(value)()
        else:
            new_value = []  # Need a mutable value
        deferred_removals.append((value, new_value))
        return new_value

    if isinstance(value, Set):
        if isinstance(value, MutableSet):
            new_value = type(value)()
        else:
            new_value = set()  # Need a mutable value
        deferred_removals.append((value, new_value))
        return new_value

    if isinstance(value, Mapping):
        if isinstance(value, MutableMapping):
            new_value = type(value)()
        else:
            new_value = {}  # Need a mutable value
        deferred_removals.append((value, new_value))
        return new_value

    if isinstance(value, (int, float, bool, NoneType)):
        return value

    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return value

    raise TypeError('Value of unknown type: %s, %s' % (type(value), value))