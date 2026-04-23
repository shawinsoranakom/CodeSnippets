def _setup_low_rank_optimizer(
    args: TrainingArguments,
    model: PreTrainedModel,
    optimizer_name: str,
    optimizer_mapping: dict[str, Any],
    optim_kwargs: dict[str, Any],
    optimizer_kwargs: dict[str, Any],
    is_layerwise_supported: bool = True,
) -> tuple[Any, dict[str, Any]]:
    """
    Helper function to set up low-rank optimizers like GaLore and Apollo.

    These optimizers apply low-rank projections to specific target modules (typically linear layers).
    """
    is_layerwise = optimizer_name.lower().endswith("layerwise")
    if is_layerwise and args.parallel_mode == ParallelMode.DISTRIBUTED and is_layerwise_supported:
        raise NotImplementedError(f"Layer-wise {optimizer_name} does not support DDP at this time")

    optimizer_cls = optimizer_mapping[optimizer_name]

    if args.optim_target_modules is None:
        raise ValueError(f"You need to define `optim_target_modules` to use {optimizer_name} optimizers")

    if not isinstance(args.optim_target_modules, (list, str)):
        raise TypeError(
            f"`optim_target_modules` must be a list of strings, a regex string, or 'all-linear'. "
            f"Got: {args.optim_target_modules}"
        )

    if model is None:
        raise ValueError(f"You need to pass a model to initialize {optimizer_name} optimizer.")

    all_linear = (
        isinstance(args.optim_target_modules, str) and args.optim_target_modules.replace("_", "-") == "all-linear"
    )

    target_params_names = []
    for module_name, module in model.named_modules():
        target_module_exists, is_regex = check_target_module_exists(
            args.optim_target_modules, module_name, return_is_regex=True
        )

        if not isinstance(module, nn.Linear):
            if target_module_exists and not is_regex:
                logger.warning(f"{module_name} matched but ignored. {optimizer_name} only supports linear layers.")
            continue

        if not target_module_exists and not all_linear:
            continue

        target_params_names.append(module_name + ".weight")

    if len(target_params_names) == 0:
        raise ValueError(f"No target modules found for {optimizer_name} ({args.optim_target_modules}).")

    target_params = [p for n, p in model.named_parameters() if n in target_params_names]
    non_target_params = [p for n, p in model.named_parameters() if n not in target_params_names]

    param_groups = [
        {"params": non_target_params},
        {"params": target_params, **optim_kwargs},
    ]

    if is_layerwise:
        if args.gradient_accumulation_steps != 1:
            raise ValueError(f"Layerwise {optimizer_name} does not support gradient accumulation!")

        optimizer_dict = {}
        for param in non_target_params:
            optimizer_dict[param] = optimizer_cls([{"params": [param]}], **optimizer_kwargs)
        for param in target_params:
            optimizer_dict[param] = optimizer_cls([{"params": [param], **optim_kwargs}], **optimizer_kwargs)

        def optimizer_hook(param):
            if param.grad is not None:
                optimizer_dict[param].step()
                optimizer_dict[param].zero_grad()

        for param in model.parameters():
            if param.requires_grad:
                param.register_post_accumulate_grad_hook(optimizer_hook)

        optimizer_cls = LayerWiseDummyOptimizer
        optimizer_kwargs.update({"optimizer_dict": optimizer_dict})

    optimizer_kwargs.update({"params": param_groups})
    return optimizer_cls, optimizer_kwargs