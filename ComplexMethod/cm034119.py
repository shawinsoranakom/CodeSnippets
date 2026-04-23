def _return_datastructure_name(obj):
    """ Return native stringified values from datastructures.

    For use with removing sensitive values pre-jsonification."""
    if isinstance(obj, (str, bytes)):
        if obj:
            yield to_native(obj, errors='surrogate_or_strict')
        return
    elif isinstance(obj, Mapping):
        for element in obj.items():
            yield from _return_datastructure_name(element[1])
    elif is_iterable(obj):
        for element in obj:
            yield from _return_datastructure_name(element)
    elif obj is None or isinstance(obj, bool):
        # This must come before int because bools are also ints
        return
    elif isinstance(obj, (int, float)):
        yield to_native(obj, nonstring='simplerepr')
    else:
        raise TypeError('Unknown parameter type: %s' % (type(obj)))