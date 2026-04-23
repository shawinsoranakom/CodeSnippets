def _remove_values_conditions(value, no_log_strings, deferred_removals):
    """
    Helper function for :meth:`remove_values`.

    :arg value: The value to check for strings that need to be stripped
    :arg no_log_strings: set of strings which must be stripped out of any values
    :arg deferred_removals: List which holds information about nested
        containers that have to be iterated for removals.  It is passed into
        this function so that more entries can be added to it if value is
        a container type.  The format of each entry is a 2-tuple where the first
        element is the ``value`` parameter and the second value is a new
        container to copy the elements of ``value`` into once iterated.

    :returns: if ``value`` is a scalar, returns ``value`` with two exceptions:

        1. :class:`~datetime.datetime` objects which are changed into a string representation.
        2. objects which are in ``no_log_strings`` are replaced with a placeholder
           so that no sensitive data is leaked.

        If ``value`` is a container type, returns a new empty container.

    ``deferred_removals`` is added to as a side-effect of this function.

    .. warning:: It is up to the caller to make sure the order in which value
        is passed in is correct.  For instance, higher level containers need
        to be passed in before lower level containers. For example, given
        ``{'level1': {'level2': 'level3': [True]} }`` first pass in the
        dictionary for ``level1``, then the dict for ``level2``, and finally
        the list for ``level3``.
    """
    original_value = value

    if isinstance(value, (str, bytes)):
        # Need native str type
        native_str_value = value
        if isinstance(value, str):
            value_is_text = True
        elif isinstance(value, bytes):
            value_is_text = False
            native_str_value = to_text(value, errors='surrogate_or_strict')

        if native_str_value in no_log_strings:
            return 'VALUE_SPECIFIED_IN_NO_LOG_PARAMETER'
        for omit_me in no_log_strings:
            native_str_value = native_str_value.replace(omit_me, '*' * 8)

        if value_is_text and isinstance(native_str_value, bytes):
            value = to_text(native_str_value, encoding='utf-8', errors='surrogate_then_replace')
        elif not value_is_text and isinstance(native_str_value, str):
            value = to_bytes(native_str_value, encoding='utf-8', errors='surrogate_then_replace')
        else:
            value = native_str_value

    elif value is True or value is False or value is None:
        return value

    elif isinstance(value, Sequence):
        new_value = AnsibleTagHelper.tag_copy(original_value, [])
        deferred_removals.append((value, new_value))
        return new_value

    elif isinstance(value, Set):
        new_value = AnsibleTagHelper.tag_copy(original_value, set())
        deferred_removals.append((value, new_value))
        return new_value

    elif isinstance(value, Mapping):
        new_value = AnsibleTagHelper.tag_copy(original_value, {})
        deferred_removals.append((value, new_value))
        return new_value

    elif isinstance(value, (int, float)):
        stringy_value = to_native(value, encoding='utf-8', errors='surrogate_or_strict')
        if stringy_value in no_log_strings:
            return 'VALUE_SPECIFIED_IN_NO_LOG_PARAMETER'
        for omit_me in no_log_strings:
            if omit_me in stringy_value:
                return 'VALUE_SPECIFIED_IN_NO_LOG_PARAMETER'

    elif isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return value
    elif isinstance(value, AnsibleSerializable):
        return value
    else:
        raise TypeError('Value of unknown type: %s, %s' % (type(value), value))

    value = AnsibleTagHelper.tag_copy(original_value, value)

    return value