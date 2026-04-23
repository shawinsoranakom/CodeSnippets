def build_nested_inputs(values: dict[str, Any], v3_data: V3Data):
    paths = v3_data.get("dynamic_paths", None)
    default_value_dict = v3_data.get("dynamic_paths_default_value", {})
    if paths is None:
        return values
    values = values.copy()

    result = {}

    create_tuple = v3_data.get("create_dynamic_tuple", False)

    for key, path in paths.items():
        parts = path.split(".")
        current = result

        for i, p in enumerate(parts):
            is_last = (i == len(parts) - 1)

            if is_last:
                value = values.pop(key, None)
                if value is None:
                    # see if a default value was provided for this key
                    default_option = default_value_dict.get(key, None)
                    if default_option == DynamicPathsDefaultValue.EMPTY_DICT:
                        value = {}
                if create_tuple:
                    value = (value, key)
                current[p] = value
            else:
                current = current.setdefault(p, {})

    values.update(result)
    return values