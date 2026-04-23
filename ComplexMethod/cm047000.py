def is_moe_model(model) -> bool:
    """
    Detect if a model is a Mixture of Experts (MoE) model.

    Args:
        model: The model to check (can be HF model or config)

    Returns:
        True if the model is an MoE model, False otherwise
    """
    config = getattr(model, "config", model)

    # Different MoE models use different config attribute names:
    # - Qwen3-MoE: num_experts
    # - GLM4-MoE: n_routed_experts, num_local_experts
    # - Mixtral: num_local_experts
    num_experts = None
    for attr in ("num_experts", "n_routed_experts", "num_local_experts"):
        num_experts = getattr(config, attr, None)
        if num_experts is not None:
            break

    # Check text_config for VL models
    if num_experts is None and hasattr(config, "text_config"):
        for attr in ("num_experts", "n_routed_experts", "num_local_experts"):
            num_experts = getattr(config.text_config, attr, None)
            if num_experts is not None:
                break

    return num_experts is not None and num_experts > 0