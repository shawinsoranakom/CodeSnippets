def get_arg_names_from_hub_spec(hub_spec, first_level=True):
    # This util is used in pipeline tests, to verify that a pipeline's documented arguments
    # match the Hub specification for that task
    arg_names = []
    for field in fields(hub_spec):
        # Recurse into nested fields, but max one level
        if is_dataclass(field.type):
            arg_names.extend([field.name for field in fields(field.type)])
            continue
        # Next, catch nested fields that are part of a Union[], which is usually caused by Optional[]
        for param_type in get_args(field.type):
            if is_dataclass(param_type):
                # Again, recurse into nested fields, but max one level
                arg_names.extend([field.name for field in fields(param_type)])
                break
        else:
            # Finally, this line triggers if it's not a nested field
            arg_names.append(field.name)
    return arg_names