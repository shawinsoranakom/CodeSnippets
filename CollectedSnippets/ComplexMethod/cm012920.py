def entry_to_pretty_str(entry) -> str:
    """
    Given a backend_config_dict entry, returns a string with the human readable
    representation of it.
    """
    s = "{\n"

    # always output the pattern first
    if "pattern" in entry:
        pattern_str = pattern_to_human_readable(entry["pattern"])

        s += f"  'pattern': {pattern_str},\n"

    # custom output for dtype_configs to make it look nice
    if "dtype_configs" in entry:
        s += "  'dtype_configs': [\n"
        for dtype_config in entry["dtype_configs"]:
            s += "    {\n"
            for k, v in dtype_config.items():
                s += f"      '{k}': {v},\n"
            s += "    },\n"
        s += "  ],\n"

    # custom output for num_tensor_args_to_observation_type to make it look nice
    if "num_tensor_args_to_observation_type" in entry:
        s += "  'num_tensor_args_to_observation_type': {\n"
        for k, v in entry["num_tensor_args_to_observation_type"].items():
            s += f"    {k}: {v},\n"
        s += "  },\n"

    # output all the other fields
    custom_handled_fields = [
        "pattern",
        "dtype_configs",
        "num_tensor_args_to_observation_type",
    ]
    for field_name in entry:
        if field_name in custom_handled_fields:
            continue
        s += f"  '{field_name}': {entry[field_name]},\n"

    s += "}"
    return s