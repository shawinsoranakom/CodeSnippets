def _apply_weight_conversions_to_state_dict(model, state_dict, weight_mapping):
    """
    Apply weight conversions (renaming and merging/splitting operations) to a state dict.
    This is a simplified version that handles the conversion without loading into the model.
    """
    # Check for Tensor Parallelism - weight conversions are not tested with TP
    # TP uses ReplaceWithTensorSlicing which may conflict with our weight conversions
    ds_config = deepspeed_config()
    if ds_config is not None:
        # Check training config (tensor_parallel.autotp_size)
        tp_size = ds_config.get("tensor_parallel", {}).get("autotp_size", 1)
        # Check inference config (inference.tensor_parallel.tp_size)
        inference_config = ds_config.get("inference", {})
        if isinstance(inference_config, dict):
            tp_size = max(tp_size, inference_config.get("tensor_parallel", {}).get("tp_size", 1))
        if tp_size > 1:
            raise NotImplementedError(
                "Weight conversions (e.g., MoE expert fusion) with DeepSpeed Tensor Parallelism "
                "are not yet implemented but support is coming soon. Please disable tensor_parallel "
                "in your DeepSpeed config or convert your checkpoint to the expected format first."
            )

    from ..core_model_loading import WeightConverter, WeightRenaming, dot_natural_key, rename_source_key

    # Preserve metadata from the original state dict
    metadata = getattr(state_dict, "_metadata", None)

    prefix = model.base_model_prefix

    # Build a meta state dict for matching - only keys/shapes, no actual tensor data
    # This minimizes memory since we don't duplicate the model's parameters
    model_state_dict = {}
    for key, param in model.state_dict().items():
        model_state_dict[key] = torch.empty(param.shape, dtype=param.dtype, device="meta")

    renamings = [entry for entry in weight_mapping if isinstance(entry, WeightRenaming)]
    converters = [entry for entry in weight_mapping if isinstance(entry, WeightConverter)]

    # Fast path: if we only have simple renamings and no converters, we can skip the expensive collection logic
    if len(converters) == 0:
        new_state_dict = {}
        for original_key, tensor in state_dict.items():
            renamed_key, _ = rename_source_key(original_key, renamings, [], prefix, model_state_dict)
            if renamed_key in model_state_dict:
                new_state_dict[renamed_key] = tensor
        # Attach metadata to the new state dict
        if metadata is not None:
            new_state_dict._metadata = metadata
        return new_state_dict

    # Full path: we have WeightConverter operations that require tensor fusion/splitting
    pattern_to_converter = {k: converter for converter in converters for k in converter.source_patterns}

    # Build a mapping of what needs to be converted
    # Sort keys to ensure consistent ordering (important for MoE conversions)
    # Iterate over sorted keys and pop from state_dict to free memory immediately
    conversion_mapping = {}
    new_state_dict = {}
    sorted_keys = sorted(state_dict.keys(), key=lambda k: dot_natural_key(k))
    for original_key in sorted_keys:
        tensor = state_dict.pop(original_key)
        renamed_key, source_pattern = rename_source_key(original_key, renamings, converters, prefix, model_state_dict)

        # Only process if the renamed key is in the model's state dict
        if renamed_key in model_state_dict:
            # If source_pattern is not None, this key needs WeightConverter (e.g., MoE fusion)
            if source_pattern is not None:
                # Create a fresh converter for this layer to hold its tensors
                # Share operations list (lightweight, no large data) but get new collected_tensors
                converter = pattern_to_converter[source_pattern]
                new_converter = WeightConverter(
                    source_patterns=converter.source_patterns,
                    target_patterns=converter.target_patterns,
                    operations=converter.operations,
                )
                mapping = conversion_mapping.setdefault(renamed_key, new_converter)
                mapping.add_tensor(renamed_key, original_key, source_pattern, tensor)
            else:
                # No conversion needed - add tensor directly to new_state_dict
                # (this handles keys like embed_tokens, lm_head, layernorm, attention)
                new_state_dict[renamed_key] = tensor

    # Apply the conversions and build the new state dict
    for renamed_key, mapping in conversion_mapping.items():
        try:
            realized_value = mapping.convert(
                renamed_key,
                model=model,
                config=model.config,
            )
            for target_name, param in realized_value.items():
                param = param[0] if isinstance(param, list) else param
                new_state_dict[target_name] = param
        except Exception as e:
            raise RuntimeError(
                f"Failed to apply weight conversion for '{renamed_key}'. "
                f"This likely means the checkpoint format is incompatible with the current model version. "
                f"Error: {e}"
            ) from e

    # Attach metadata to the new state dict
    if metadata is not None:
        new_state_dict._metadata = metadata

    return new_state_dict