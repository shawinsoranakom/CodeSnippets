def find_all_linear_modules(model: "PreTrainedModel", freeze_vision_tower: bool) -> list[str]:
    r"""Find all available modules to apply LoRA, GaLore or APOLLO."""
    model_type = getattr(model.config, "model_type", None)
    forbidden_modules = {"lm_head"}
    if model_type == "chatglm":
        forbidden_modules.add("output_layer")
    elif model_type == "internlm2":
        forbidden_modules.add("output")

    if model_type in COMPOSITE_MODELS:
        forbidden_modules.update(COMPOSITE_MODELS[model_type].projector_keys)

    if freeze_vision_tower and model_type in COMPOSITE_MODELS:
        forbidden_modules.update(COMPOSITE_MODELS[model_type].vision_model_keys)

    module_names = set()
    for name, module in model.named_modules():
        if any(forbidden_module in name for forbidden_module in forbidden_modules):
            continue

        if "Linear" in module.__class__.__name__ and "Embedding" not in module.__class__.__name__:
            module_names.add(name.split(".")[-1])

    logger.info_rank0("Found linear modules: {}".format(",".join(module_names)))
    return list(module_names)