def _list_no_log_values(argument_spec, params):
    """Return set of no log values

    :arg argument_spec: An argument spec dictionary
    :arg params: Dictionary of all parameters

    :returns: :class:`set` of strings that should be hidden from output:
    """

    no_log_values = set()
    for arg_name, arg_opts in argument_spec.items():
        if arg_opts.get('no_log', False):
            # Find the value for the no_log'd param
            no_log_object = params.get(arg_name, None)

            if no_log_object:
                try:
                    no_log_values.update(_return_datastructure_name(no_log_object))
                except TypeError as e:
                    raise TypeError('Failed to convert "%s": %s' % (arg_name, to_native(e)))

        # Get no_log values from suboptions
        sub_argument_spec = arg_opts.get('options')
        if sub_argument_spec is not None:
            wanted_type = arg_opts.get('type')
            sub_parameters = params.get(arg_name)

            if sub_parameters is not None:
                if wanted_type == 'dict' or (wanted_type == 'list' and arg_opts.get('elements', '') == 'dict'):
                    # Sub parameters can be a dict or list of dicts. Ensure parameters are always a list.
                    if not isinstance(sub_parameters, list):
                        sub_parameters = [sub_parameters]

                    for sub_param in sub_parameters:
                        # Validate dict fields in case they came in as strings

                        if isinstance(sub_param, str):
                            sub_param = check_type_dict(sub_param)

                        if not isinstance(sub_param, Mapping):
                            raise TypeError("Value '{1}' in the sub parameter field '{0}' must be a {2}, "
                                            "not '{1.__class__.__name__}'".format(arg_name, sub_param, wanted_type))

                        no_log_values.update(_list_no_log_values(sub_argument_spec, sub_param))

    return no_log_values