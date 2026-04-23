def _validate_argument_types(argument_spec, parameters, prefix='', options_context=None, errors=None):
    """Validate that parameter types match the type in the argument spec.

    Determine the appropriate type checker function and run each
    parameter value through that function. All error messages from type checker
    functions are returned. If any parameter fails to validate, it will not
    be in the returned parameters.

    :arg argument_spec: Argument spec
    :type argument_spec: dict

    :arg parameters: Parameters
    :type parameters: dict

    :kwarg prefix: Name of the parent key that contains the spec. Used in the error message
    :type prefix: str

    :kwarg options_context: List of contexts?
    :type options_context: list

    :returns: Two item tuple containing validated and coerced parameters
              and a list of any errors that were encountered.
    :rtype: tuple

    """

    if errors is None:
        errors = AnsibleValidationErrorMultiple()

    for param, spec in argument_spec.items():
        if param not in parameters:
            continue

        value = parameters[param]
        if value is None and not spec.get('required') and spec.get('default') is None:
            continue

        wanted_type = spec.get('type')
        type_checker, wanted_name = _get_type_validator(wanted_type)
        # Get param name for strings so we can later display this value in a useful error message if needed
        # Only pass 'kwargs' to our checkers and ignore custom callable checkers
        kwargs = {}
        if wanted_name == 'str' and isinstance(wanted_type, str):
            kwargs['param'] = list(parameters.keys())[0]

            # Get the name of the parent key if this is a nested option
            if prefix:
                kwargs['prefix'] = prefix

        try:
            parameters[param] = type_checker(value, **kwargs)
            elements_wanted_type = spec.get('elements', None)
            if elements_wanted_type:
                elements = parameters[param]
                if not isinstance(parameters[param], list) or not isinstance(elements, list):
                    msg = "Invalid type %s for option '%s'" % (wanted_name, elements)
                    if options_context:
                        msg += " found in '%s'." % " -> ".join(options_context)
                    msg += ", elements value check is supported only with 'list' type"
                    errors.append(ArgumentTypeError(msg))
                parameters[param] = _validate_elements(elements_wanted_type, param, elements, options_context, errors)

        except (TypeError, ValueError) as e:
            msg = "argument '%s' is of type %s" % (param, native_type_name(value))
            if options_context:
                msg += " found in '%s'." % " -> ".join(options_context)
            msg += " and we were unable to convert to %s: %s" % (wanted_name, to_native(e))
            errors.append(ArgumentTypeError(msg))