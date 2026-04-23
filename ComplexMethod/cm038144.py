def _build_rope_parameters(config: PretrainedConfig) -> dict | None:
    rope_parameters = copy.deepcopy(getattr(config, "rope_parameters", None)) or {}
    if "rope_theta" not in rope_parameters and hasattr(config, "rope_theta"):
        rope_parameters["rope_theta"] = config.rope_theta
    if "partial_rotary_factor" not in rope_parameters and hasattr(
        config, "partial_rotary_factor"
    ):
        rope_parameters["partial_rotary_factor"] = config.partial_rotary_factor

    rope_scaling = getattr(config, "rope_scaling", None)
    if isinstance(rope_scaling, dict):
        rope_scaling = copy.deepcopy(rope_scaling)
        if "type" in rope_scaling and "rope_type" not in rope_scaling:
            rope_scaling["rope_type"] = rope_scaling.pop("type")
        rope_parameters.update(rope_scaling)

    return rope_parameters or None