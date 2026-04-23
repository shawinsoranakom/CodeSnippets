def _handle_aliases(argument_spec, parameters, alias_warnings=None, alias_deprecations=None):
    """Process aliases from an argument_spec including warnings and deprecations.

    Modify ``parameters`` by adding a new key for each alias with the supplied
    value from ``parameters``.

    If a list is provided to the alias_warnings parameter, it will be filled with tuples
    (option, alias) in every case where both an option and its alias are specified.

    If a list is provided to alias_deprecations, it will be populated with dictionaries,
    each containing deprecation information for each alias found in argument_spec.

    :param argument_spec: Dictionary of parameters, their type, and valid values.
    :type argument_spec: dict

    :param parameters: Dictionary of parameters.
    :type parameters: dict

    :param alias_warnings:
    :type alias_warnings: list

    :param alias_deprecations:
    :type alias_deprecations: list
    """

    aliases_results = {}  # alias:canon

    for (k, v) in argument_spec.items():
        aliases = v.get('aliases', None)
        default = v.get('default', None)
        required = v.get('required', False)

        if alias_deprecations is not None:
            for alias in argument_spec[k].get('deprecated_aliases', []):
                if alias.get('name') in parameters:
                    alias_deprecations.append(alias)

        if default is not None and required:
            # not alias specific but this is a good place to check this
            raise ValueError("internal error: required and default are mutually exclusive for %s" % k)

        if aliases is None:
            continue

        if not is_iterable(aliases) or isinstance(aliases, (bytes, str)):
            raise TypeError('internal error: aliases must be a list or tuple')

        for alias in aliases:
            aliases_results[alias] = k
            if alias in parameters:
                if k in parameters and alias_warnings is not None:
                    alias_warnings.append((k, alias))
                parameters[k] = parameters[alias]

    return aliases_results