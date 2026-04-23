def _verify_target_data_type(features_dict, target_columns):
    # verifies the data type of the y array in case there are multiple targets
    # (throws an error if these targets do not comply with sklearn support)
    if not isinstance(target_columns, list):
        raise ValueError("target_column should be list, got: %s" % type(target_columns))
    found_types = set()
    for target_column in target_columns:
        if target_column not in features_dict:
            raise KeyError(f"Could not find target_column='{target_column}'")
        if features_dict[target_column]["data_type"] == "numeric":
            found_types.add(np.float64)
        else:
            found_types.add(object)

        # note: we compare to a string, not boolean
        if features_dict[target_column]["is_ignore"] == "true":
            warn(f"target_column='{target_column}' has flag is_ignore.")
        if features_dict[target_column]["is_row_identifier"] == "true":
            warn(f"target_column='{target_column}' has flag is_row_identifier.")
    if len(found_types) > 1:
        raise ValueError(
            "Can only handle homogeneous multi-target datasets, "
            "i.e., all targets are either numeric or "
            "categorical."
        )