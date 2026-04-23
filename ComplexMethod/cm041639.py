def get_freeze_model(model: HFModel, config: FreezeConfigDict, is_train: bool = False) -> HFModel:
    logger.info_rank0("Fine-tuning method: Freeze")

    if not is_train:
        return model

    freeze_trainable_layers = config.get("freeze_trainable_layers", 2)
    freeze_trainable_modules = config.get("freeze_trainable_modules", ["all"])
    freeze_extra_modules = config.get("freeze_extra_modules", [])
    cast_trainable_params_to_fp32 = config.get("cast_trainable_params_to_fp32", True)

    if isinstance(freeze_trainable_modules, str):
        freeze_trainable_modules = [module.strip() for module in freeze_trainable_modules.split(",")]

    if isinstance(freeze_extra_modules, str):
        freeze_extra_modules = [module.strip() for module in freeze_extra_modules.split(",")]

    # Get number of layers
    num_layers = (
        getattr(model.config, "num_hidden_layers", None)
        or getattr(model.config, "num_layers", None)
        or getattr(model.config, "n_layer", None)
    )

    if not num_layers:
        raise ValueError("Current model does not support freeze tuning.")

    if freeze_trainable_layers > 0:
        # last n layers
        trainable_layer_ids = range(max(0, num_layers - freeze_trainable_layers), num_layers)
    else:
        # first n layers
        trainable_layer_ids = range(min(-freeze_trainable_layers, num_layers))

    # Identify hidden and non-hidden modules
    hidden_modules = set()
    non_hidden_modules = set()
    for name, _ in model.named_parameters():
        if ".0." in name:
            hidden_modules.add(name.split(".0.")[-1].split(".")[0])
        elif ".1." in name:
            hidden_modules.add(name.split(".1.")[-1].split(".")[0])

        if re.search(r"\.\d+\.", name) is None:
            non_hidden_modules.add(name.split(".")[-2])

    # Build list of trainable layer patterns
    trainable_layers = []
    for module_name in freeze_trainable_modules:
        if module_name == "all":
            for idx in trainable_layer_ids:
                trainable_layers.append(f".{idx:d}.")
        elif module_name in hidden_modules:
            for idx in trainable_layer_ids:
                trainable_layers.append(f".{idx:d}.{module_name}")
        else:
            raise ValueError(f"Module {module_name} not found in hidden modules: {hidden_modules}")

    # Add extra modules
    if freeze_extra_modules:
        for module_name in freeze_extra_modules:
            if module_name in non_hidden_modules:
                trainable_layers.append(module_name)
            else:
                raise ValueError(f"Module {module_name} not found in non-hidden modules: {non_hidden_modules}")

    # TODO
    # Multi-modal special handling

    # Set requires_grad
    forbidden_modules = {"quant_state", "quantization_weight", "qweight", "qzeros", "scales"}
    for name, param in model.named_parameters():
        if any(trainable_layer in name for trainable_layer in trainable_layers) and not any(
            forbidden_module in name for forbidden_module in forbidden_modules
        ):
            param.requires_grad_(True)
            if cast_trainable_params_to_fp32:
                param.data = param.data.to(torch.float32)  # Cast to fp32 for stability
        else:
            param.requires_grad_(False)

    logger.info_rank0(f"Set trainable layers: {trainable_layers}")

    # Count trainable params for verification
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    all_params = sum(p.numel() for p in model.parameters())
    logger.info_rank0(
        f"trainable params: {trainable_params} || all params: {all_params} || trainable%: {100 * trainable_params / all_params:.4f}"
    )

    return model