def get_moe_target_parameters(model, target_modules = None) -> Optional[List[str]]:
    """
    Get the target_parameters for MoE expert layers if applicable.

    For MoE models, returns the parameter paths for expert weights
    (gate_up_proj, down_proj) that should be targeted by PEFT's
    target_parameters for LoRA on nn.Parameter. The exact parameter path
    depends on the model layout, for example ``mlp.experts.*`` or
    ``experts.*``.

    Only includes MoE parameters that match what's in target_modules:
    - If "down_proj" is in target_modules -> includes "mlp.experts.down_proj"
    - If "gate_proj" or "up_proj" is in target_modules -> includes "mlp.experts.gate_up_proj"

    Args:
        model: The model to get target parameters for
        target_modules: List/tuple of target module names to match against

    Returns:
        List of parameter paths for MoE experts, or None if not an MoE model
    """
    if not is_moe_model(model):
        return None

    config = getattr(model, "config", model)
    # Get num_experts from various possible config attributes
    num_experts = None
    for attr in ("num_experts", "n_routed_experts", "num_local_experts"):
        num_experts = getattr(config, attr, None)
        if num_experts is not None:
            break
    if num_experts is None and hasattr(config, "text_config"):
        for attr in ("num_experts", "n_routed_experts", "num_local_experts"):
            num_experts = getattr(config.text_config, attr, None)
            if num_experts is not None:
                break
    if num_experts is None:
        num_experts = 0

    # Determine which MoE parameters to include based on target_modules
    moe_params = []

    # Normalize target_modules to a set for efficient lookup
    if target_modules is None:
        # If no target_modules specified, include all MoE params
        target_set = {"gate_proj", "up_proj", "down_proj", "gate_up_proj"}
    elif isinstance(target_modules, str):
        target_set = {target_modules}
        # Heuristic for regex matching MLPs
        if "proj" in target_modules and (
            "mlp" in target_modules or "ffn" in target_modules
        ):
            target_set.update({"gate_proj", "up_proj", "down_proj", "gate_up_proj"})
    else:
        target_set = set(target_modules) if target_modules else set()

    gate_up_name = _resolve_moe_parameter_name(
        model,
        default_name = "mlp.experts.gate_up_proj",
        alternate_name = "experts.gate_up_proj",
    )
    down_name = _resolve_moe_parameter_name(
        model,
        default_name = "mlp.experts.down_proj",
        alternate_name = "experts.down_proj",
    )

    # gate_up_proj combines both gate_proj and up_proj in MoE
    # Also match "gate_up_proj" directly since users may specify the fused name
    if (
        "gate_proj" in target_set
        or "up_proj" in target_set
        or "gate_up_proj" in target_set
    ):
        moe_params.append(gate_up_name)

    if "down_proj" in target_set:
        moe_params.append(down_name)

    if moe_params:
        print(
            f"Unsloth: Detected MoE model with {num_experts = } and {target_modules = }. Enabling LoRA on MoE parameters: {moe_params}"
        )
        return moe_params

    return None