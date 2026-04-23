def _validate_argument_values(argument_spec, parameters, options_context=None, errors=None):
    """Ensure all arguments have the requested values, and there are no stray arguments"""

    if errors is None:
        errors = AnsibleValidationErrorMultiple()

    for param, spec in argument_spec.items():
        choices = spec.get('choices')
        if choices is None:
            continue

        if isinstance(choices, (frozenset, KeysView, Sequence)) and not isinstance(choices, (bytes, str)):
            if param in parameters:
                # Allow one or more when type='list' param with choices
                if isinstance(parameters[param], list):
                    diff_list = [item for item in parameters[param] if item not in choices]
                    if diff_list:
                        choices_str = ", ".join([to_native(c) for c in choices])
                        diff_str = ", ".join([to_native(c) for c in diff_list])
                        msg = "value of %s must be one or more of: %s. Got no match for: %s" % (param, choices_str, diff_str)
                        if options_context:
                            msg = "{0} found in {1}".format(msg, " -> ".join(options_context))
                        errors.append(ArgumentValueError(msg))
                elif parameters[param] not in choices:
                    # PyYaml converts certain strings to bools. If we can unambiguously convert back, do so before checking
                    # the value. If we can't figure this out, module author is responsible.
                    if parameters[param] == 'False':
                        overlap = BOOLEANS_FALSE.intersection(choices)
                        if len(overlap) == 1:
                            # Extract from a set
                            (parameters[param],) = overlap

                    if parameters[param] == 'True':
                        overlap = BOOLEANS_TRUE.intersection(choices)
                        if len(overlap) == 1:
                            (parameters[param],) = overlap

                    if parameters[param] not in choices:
                        choices_str = ", ".join([to_native(c) for c in choices])
                        msg = "value of %s must be one of: %s, got: %s" % (param, choices_str, parameters[param])
                        if options_context:
                            msg = "{0} found in {1}".format(msg, " -> ".join(options_context))
                        errors.append(ArgumentValueError(msg))
        else:
            msg = "internal error: choices for argument %s are not iterable: %s" % (param, choices)
            if options_context:
                msg = "{0} found in {1}".format(msg, " -> ".join(options_context))
            errors.append(ArgumentTypeError(msg))