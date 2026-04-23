def sanitize_keys(obj, no_log_strings, ignore_keys=frozenset()):
    """Sanitize the keys in a container object by removing ``no_log`` values from key names.

    This is a companion function to the :func:`remove_values` function. Similar to that function,
    we make use of ``deferred_removals`` to avoid hitting maximum recursion depth in cases of
    large data structures.

    :arg obj: The container object to sanitize. Non-container objects are returned unmodified.
    :arg no_log_strings: A set of string values we do not want logged.
    :kwarg ignore_keys: A set of string values of keys to not sanitize.

    :returns: An object with sanitized keys.
    """

    deferred_removals = deque()

    no_log_strings = [to_native(s, errors='surrogate_or_strict') for s in no_log_strings]
    new_value = _sanitize_keys_conditions(obj, no_log_strings, ignore_keys, deferred_removals)

    while deferred_removals:
        old_data, new_data = deferred_removals.popleft()

        if isinstance(new_data, Mapping):
            for old_key, old_elem in old_data.items():
                if old_key in ignore_keys or old_key.startswith('_ansible'):
                    new_data[old_key] = _sanitize_keys_conditions(old_elem, no_log_strings, ignore_keys, deferred_removals)
                else:
                    # Sanitize the old key. We take advantage of the sanitizing code in
                    # _remove_values_conditions() rather than recreating it here.
                    new_key = _remove_values_conditions(old_key, no_log_strings, None)
                    new_data[new_key] = _sanitize_keys_conditions(old_elem, no_log_strings, ignore_keys, deferred_removals)
        else:
            for elem in old_data:
                new_elem = _sanitize_keys_conditions(elem, no_log_strings, ignore_keys, deferred_removals)
                if isinstance(new_data, MutableSequence):
                    new_data.append(new_elem)
                elif isinstance(new_data, MutableSet):
                    new_data.add(new_elem)
                else:
                    raise TypeError('Unknown container type encountered when removing private values from keys')

    return new_value