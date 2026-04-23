def compare_pipeline_output_to_hub_spec(output, hub_spec):
    missing_keys = []
    unexpected_keys = []
    all_field_names = {field.name for field in fields(hub_spec)}
    matching_keys = sorted([key for key in output if key in all_field_names])

    # Fields with a MISSING default are required and must be in the output
    for field in fields(hub_spec):
        if field.default is MISSING and field.name not in output:
            missing_keys.append(field.name)

    # All output keys must match either a required or optional field in the Hub spec
    for output_key in output:
        if output_key not in all_field_names:
            unexpected_keys.append(output_key)

    if missing_keys or unexpected_keys:
        error = ["Pipeline output does not match Hub spec!"]
        if matching_keys:
            error.append(f"Matching keys: {matching_keys}")
        if missing_keys:
            error.append(f"Missing required keys in pipeline output: {missing_keys}")
        if unexpected_keys:
            error.append(f"Keys in pipeline output that are not in Hub spec: {unexpected_keys}")
        raise KeyError("\n".join(error))