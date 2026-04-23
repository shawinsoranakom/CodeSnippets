def revert_weight_conversion(model: PreTrainedModel, state_dict: dict[str, torch.Tensor]):
    """
    Revert the conversion mapping that was used to load the model with `from_pretrained`, or the default one
    if the model was created in another way and is part of the default mappings.
    """
    weight_conversions = getattr(model, "_weight_conversions", None)
    # In this case, the model was not created with `from_pretrained` -> let's check if it's in the hardcoded
    # mappings, and recreate the mapping from there if it is
    if weight_conversions is None:
        from .conversion_mapping import get_model_conversion_mapping

        # Do not resave with the legacy renaming, if present
        weight_conversions = get_model_conversion_mapping(model, add_legacy=False)
        # If the model had no `_weight_conversions` attached, drop any PrefixChange transform - this is because the
        # model was almost surely instantiated from scratch (at least not from `from_pretrained`), and PrefixChange with
        # `prefix_to_remove` would otherwise add a unwanted prefix (as we dont have any information about whether the prefix
        # was there or not during load)
        weight_conversions = [x for x in weight_conversions if not isinstance(x, PrefixChange)]
        weight_conversions = weight_conversions if len(weight_conversions) > 0 else None

    # We did not find any operations to perform -> quick escape
    if weight_conversions is None:
        return state_dict

    # Important: we need to revert the order here, so that potential conversions from submodels are performed first
    weight_conversions = weight_conversions[::-1]

    # Reverse all Transform to correctly match keys
    reverse_weight_conversion = [conversion.reverse_transform() for conversion in weight_conversions]
    # If we are still here, we need to create the (reverse) conversion mapping from scratch
    renamings = [entry for entry in reverse_weight_conversion if isinstance(entry, WeightRenaming)]
    converters = [entry for entry in reverse_weight_conversion if isinstance(entry, WeightConverter)]
    pattern_to_converter = {k: converter for converter in converters for k in converter.source_patterns}
    conversion_mapping = {}

    state_dict = sorted(state_dict.items(), key=lambda kv: dot_natural_key(kv[0]))
    for original_key, tensor in state_dict:
        # Rename the key according to all renaming pattern and optional weight converter patterns
        renamed_key, source_pattern = rename_source_key(original_key, renamings, converters)
        if source_pattern is not None:
            new_converter = deepcopy(pattern_to_converter[source_pattern])
            # each target key gets its own converter instance
            mapping = conversion_mapping.setdefault(renamed_key, new_converter)
        else:
            mapping = conversion_mapping.setdefault(renamed_key, WeightRenaming(original_key, renamed_key))
            source_pattern = original_key

        mapping.add_tensor(renamed_key, original_key, source_pattern, tensor)

    new_state_dict = {}
    for first_param_name, reversed_converter in conversion_mapping.items():
        # Apply the reverse converter
        realized_value = reversed_converter.convert(first_param_name, model=model, config=model.config)
        for target_name, param in realized_value.items():
            param = param[0] if isinstance(param, list) else param
            new_state_dict[target_name] = param

    return new_state_dict