def set_fallbacks(argument_spec, parameters):
    no_log_values = set()
    for param, value in argument_spec.items():
        fallback = value.get('fallback', (None,))
        fallback_strategy = fallback[0]
        fallback_args = []
        fallback_kwargs = {}
        if param not in parameters and fallback_strategy is not None:
            for item in fallback[1:]:
                if isinstance(item, dict):
                    fallback_kwargs = item
                else:
                    fallback_args = item
            try:
                fallback_value = fallback_strategy(*fallback_args, **fallback_kwargs)
            except AnsibleFallbackNotFound:
                continue
            else:
                if value.get('no_log', False) and fallback_value:
                    no_log_values.add(fallback_value)
                parameters[param] = fallback_value

    return no_log_values