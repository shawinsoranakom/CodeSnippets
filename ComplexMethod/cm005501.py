def _convert_peft_config_moe(peft_config, model_type: str):
    base_model_type = _MODEL_TO_CONVERSION_PATTERN.get(model_type, None)
    if base_model_type is None:
        return peft_config

    target_module_mapping = _MOE_TARGET_MODULE_MAPPING.get(base_model_type)
    if target_module_mapping is None:
        # Non-MoE architectures reuse _MODEL_TO_CONVERSION_PATTERN for key renaming only.
        return peft_config
    fused_targets = _MOE_FUSED_TARGETS.get(base_model_type, {})

    peft_config.target_parameters = set(peft_config.target_parameters or [])
    peft_config.target_modules = set(peft_config.target_modules or [])
    if not hasattr(peft_config, "rank_pattern") or peft_config.rank_pattern is None:
        peft_config.rank_pattern = {}
    if not hasattr(peft_config, "alpha_pattern") or peft_config.alpha_pattern is None:
        peft_config.alpha_pattern = {}

    new_target_parameters = peft_config.target_parameters.copy()
    remaining_target_modules = set()
    matched_targets: dict[str, set[str]] = {new_name: set() for new_name in fused_targets}

    for target in peft_config.target_modules:
        mapped_new_name = None
        mapped_old_name = None
        for old_name, new_name in target_module_mapping.items():
            if (target == old_name) or target.endswith(f".{old_name}"):
                mapped_new_name = new_name
                mapped_old_name = old_name
                break

        if mapped_new_name is None:
            remaining_target_modules.add(target)
            continue

        new_target_parameters.add(mapped_new_name)
        if mapped_new_name in fused_targets and mapped_old_name is not None:
            matched_targets.setdefault(mapped_new_name, set()).add(mapped_old_name)

    for new_name, required_old_targets in fused_targets.items():
        present_targets = matched_targets.get(new_name, set())
        if 0 < len(present_targets) < len(required_old_targets):
            missing = ", ".join(sorted(required_old_targets - present_targets))
            present = ", ".join(sorted(present_targets))
            raise ValueError(
                f"Cannot convert PEFT target(s) {present} without also targeting {missing} because they are fused into {new_name}."
            )

        if len(present_targets) == len(required_old_targets) and len(required_old_targets) > 1:
            peft_config.rank_pattern[rf".*\.{re.escape(new_name)}"] = peft_config.r * len(required_old_targets)
            # Preserve per-branch LoRA scaling after fusion.
            # Example: w1 + w3 => r doubles, so alpha must also double to keep alpha/r unchanged.
            peft_config.alpha_pattern[rf".*\.{re.escape(new_name)}"] = peft_config.lora_alpha * len(
                required_old_targets
            )

    peft_config.target_parameters = new_target_parameters
    peft_config.target_modules = remaining_target_modules

    return peft_config