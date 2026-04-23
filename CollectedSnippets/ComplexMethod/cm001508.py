def get_override_settings(params, *, skip_fields=None):
    """Returns a list of settings overrides from the infotext parameters dictionary.

    This function checks the `params` dictionary for any keys that correspond to settings in `shared.opts` and returns
    a list of tuples containing the parameter name, setting name, and new value cast to correct type.

    It checks for conditions before adding an override:
    - ignores settings that match the current value
    - ignores parameter keys present in skip_fields argument.

    Example input:
        {"Clip skip": "2"}

    Example output:
        [("Clip skip", "CLIP_stop_at_last_layers", 2)]
    """

    res = []

    mapping = [(info.infotext, k) for k, info in shared.opts.data_labels.items() if info.infotext]
    for param_name, setting_name in mapping + infotext_to_setting_name_mapping:
        if param_name in (skip_fields or {}):
            continue

        v = params.get(param_name, None)
        if v is None:
            continue

        if setting_name == "sd_model_checkpoint" and shared.opts.disable_weights_auto_swap:
            continue

        v = shared.opts.cast_value(setting_name, v)
        current_value = getattr(shared.opts, setting_name, None)

        if v == current_value:
            continue

        res.append((param_name, setting_name, v))

    return res