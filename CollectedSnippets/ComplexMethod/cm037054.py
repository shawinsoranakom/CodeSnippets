def patch_rope_parameters(config: PretrainedConfig) -> None:
    """Provide backwards compatibility for RoPE."""
    from vllm.config.utils import getattr_iter

    # Older custom models may use non-standard field names
    # which need patching for both Transformers v4 and v5.
    names = ["rope_theta", "rotary_emb_base"]
    rope_theta = getattr_iter(config, names, None, warn=True)
    names = ["partial_rotary_factor", "rotary_pct", "rotary_emb_fraction"]
    partial_rotary_factor = getattr_iter(config, names, None, warn=True)
    ompe = getattr(config, "original_max_position_embeddings", None)

    if Version(version("transformers")) < Version("5.0.0"):
        # Transformers v4 installed, legacy config fields may be present
        if (rope_scaling := getattr(config, "rope_scaling", None)) is not None:
            config.rope_parameters = rope_scaling
        if (
            rope_theta is not None
            or partial_rotary_factor is not None
            or ompe is not None
        ) and not getattr(config, "rope_parameters", None):
            config.rope_parameters = {"rope_type": "default"}
        # Patch legacy fields into rope_parameters
        if rope_theta is not None:
            config.rope_parameters["rope_theta"] = rope_theta
        if partial_rotary_factor is not None:
            config.rope_parameters["partial_rotary_factor"] = partial_rotary_factor
        if ompe is not None:
            config.rope_parameters["original_max_position_embeddings"] = ompe
    elif rope_theta is not None or getattr(config, "rope_parameters", None):
        # Transformers v5 installed
        # Patch these fields in case they used non-standard names
        if rope_theta is not None:
            config.rope_theta = rope_theta
        if partial_rotary_factor is not None:
            config.partial_rotary_factor = partial_rotary_factor
        # Standardize and validate RoPE parameters
        config.standardize_rope_params()
        config.validate_rope()

    # No RoPE parameters to patch
    if getattr(config, "rope_parameters", None) is None:
        return

    # Handle nested rope_parameters in interleaved sliding attention models
    if is_rope_parameters_nested(config.rope_parameters):
        for rope_parameters_layer_type in config.rope_parameters.values():
            patch_rope_parameters_dict(rope_parameters_layer_type)
    else:
        patch_rope_parameters_dict(config.rope_parameters)