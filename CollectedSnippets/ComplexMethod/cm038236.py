def _get_rope_parameters(config) -> dict[str, Any] | None:
    rope_parameters = getattr(config, "rope_parameters", None)
    if rope_parameters is None:
        rope_type = getattr(config, "rope_type", None)
        if rope_type is None:
            return None
        rope_parameters = {"rope_type": rope_type}
        rope_theta = getattr(config, "rope_theta", None)
        if rope_theta is not None:
            rope_parameters["rope_theta"] = rope_theta
        scaling_factor = getattr(config, "scaling_factor", None)
        if scaling_factor is not None:
            rope_parameters["factor"] = scaling_factor
        for name in (
            "original_max_position_embeddings",
            "extrapolation_factor",
            "attn_factor",
            "beta_fast",
            "beta_slow",
        ):
            value = getattr(config, name, None)
            if value is not None:
                rope_parameters[name] = value

    if rope_parameters.get("rope_type") == "original":
        rope_parameters = dict(rope_parameters)
        rope_parameters["rope_type"] = "default"
    return rope_parameters