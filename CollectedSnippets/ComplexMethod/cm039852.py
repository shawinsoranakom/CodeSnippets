def _check_param_lengths(required, optional, class_name):
    """Check required and optional parameters are of the same length."""
    optional_provided = {}
    for name, param in optional.items():
        if isinstance(param, list):
            optional_provided[name] = param

    all_params = {**required, **optional_provided}
    if len({len(param) for param in all_params.values()}) > 1:
        param_keys = [key for key in all_params.keys()]
        # Note: below code requires `len(param_keys) >= 2`, which is the case for all
        # display classes
        params_formatted = " and ".join([", ".join(param_keys[:-1]), param_keys[-1]])
        or_plot = ""
        if "'name' (or self.name)" in param_keys:
            or_plot = " (or `plot`)"
        lengths_formatted = ", ".join(
            f"{key}: {len(value)}" for key, value in all_params.items()
        )
        raise ValueError(
            f"{params_formatted} from `{class_name}` initialization{or_plot}, "
            f"should all be lists of the same length. Got: {lengths_formatted}"
        )