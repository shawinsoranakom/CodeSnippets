def check_required_by(requirements, parameters, options_context=None):
    """For each key in requirements, check the corresponding list to see if they
    exist in parameters.

    Accepts a single string or list of values for each key.

    :arg requirements: Dictionary of requirements
    :arg parameters: Dictionary of parameters
    :kwarg options_context: List of strings of parent key names if ``requirements`` are
        in a sub spec.

    :returns: Empty dictionary or raises :class:`TypeError` if the check fails.
    """

    result = {}
    if requirements is None:
        return result

    for (key, value) in requirements.items():
        if key not in parameters or parameters[key] is None:
            continue
        # Support strings (single-item lists)
        if isinstance(value, str):
            value = [value]

        if missing := [required for required in value if required not in parameters or parameters[required] is None]:
            msg = f"missing parameter(s) required by '{key}': {', '.join(missing)}"
            if options_context:
                msg = f"{msg} found in {' -> '.join(options_context)}"
            raise TypeError(to_native(msg))
    return result