def _validate_elements(wanted_type, parameter, values, options_context=None, errors=None):

    if errors is None:
        errors = AnsibleValidationErrorMultiple()

    type_checker, wanted_element_type = _get_type_validator(wanted_type)
    validated_parameters = []
    # Get param name for strings so we can later display this value in a useful error message if needed
    # Only pass 'kwargs' to our checkers and ignore custom callable checkers
    kwargs = {}
    if wanted_element_type == 'str' and isinstance(wanted_type, str):
        if isinstance(parameter, str):
            kwargs['param'] = parameter
        elif isinstance(parameter, dict):
            kwargs['param'] = list(parameter.keys())[0]

    for value in values:
        try:
            validated_parameters.append(type_checker(value, **kwargs))
        except (TypeError, ValueError) as e:
            msg = "Elements value for option '%s'" % parameter
            if options_context:
                msg += " found in '%s'" % " -> ".join(options_context)
            msg += " is of type %s and we were unable to convert to %s: %s" % (native_type_name(value), wanted_element_type, to_native(e))
            errors.append(ElementError(msg))
    return validated_parameters