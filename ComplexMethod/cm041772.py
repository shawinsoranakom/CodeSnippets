def _create_apollo_optimizer(
    model: "PreTrainedModel",
    training_args: "TrainingArguments",
    finetuning_args: "FinetuningArguments",
) -> "torch.optim.Optimizer":
    if len(finetuning_args.apollo_target) == 1 and finetuning_args.apollo_target[0] == "all":
        apollo_targets = find_all_linear_modules(model, finetuning_args.freeze_vision_tower)
    else:
        apollo_targets = finetuning_args.apollo_target

    apollo_params: list[torch.nn.Parameter] = []
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.Linear) and any(target in name for target in apollo_targets):
            for param in module.parameters():
                if param.requires_grad and len(param.shape) > 1:
                    apollo_params.append(param)

    apollo_kwargs = {
        "rank": finetuning_args.apollo_rank,
        "proj": finetuning_args.apollo_proj,
        "proj_type": finetuning_args.apollo_proj_type,
        "update_proj_gap": finetuning_args.apollo_update_interval,
        "scale": finetuning_args.apollo_scale,
        "scale_type": finetuning_args.apollo_scale_type,
        "scale_front": finetuning_args.apollo_scale_front,
    }

    id_apollo_params = {id(param) for param in apollo_params}
    decay_params, nodecay_params = [], []  # they are non-apollo parameters
    trainable_params: list[torch.nn.Parameter] = []  # apollo_params + decay_params + nodecay_params
    decay_param_names = _get_decay_parameter_names(model)
    for name, param in model.named_parameters():
        if param.requires_grad:
            trainable_params.append(param)
            if id(param) not in id_apollo_params:
                if name in decay_param_names:
                    decay_params.append(param)
                else:
                    nodecay_params.append(param)

    _, optim_kwargs = Trainer.get_optimizer_cls_and_kwargs(training_args)

    if training_args.optim == "adamw_torch":
        optim_class = APOLLOAdamW
    else:
        raise NotImplementedError(f"Unknown optim: {training_args.optim}.")

    if finetuning_args.apollo_layerwise:
        logger.warning_rank0("The displayed gradient norm will be all zeros in layerwise APOLLO.")
        if training_args.gradient_accumulation_steps != 1:
            raise ValueError("Per-layer APOLLO does not support gradient accumulation.")

        optimizer_dict: dict[torch.Tensor, torch.optim.Optimizer] = {}
        for param in nodecay_params:
            param_groups = [dict(params=[param], weight_decay=0.0)]
            optimizer_dict[param] = optim_class(param_groups, **optim_kwargs)
        for param in decay_params:
            param_groups = [dict(params=[param], weight_decay=training_args.weight_decay)]
            optimizer_dict[param] = optim_class(param_groups, **optim_kwargs)
        for param in apollo_params:  # apollo params have weight decay
            param_groups = [dict(params=[param], weight_decay=training_args.weight_decay, **apollo_kwargs)]
            optimizer_dict[param] = optim_class(param_groups, **optim_kwargs)

        def optimizer_hook(param: "torch.nn.Parameter"):
            if param.grad is not None:
                optimizer_dict[param].step()
                optimizer_dict[param].zero_grad()

        for param in trainable_params:
            param.register_post_accumulate_grad_hook(optimizer_hook)

        optimizer = DummyOptimizer(lr=training_args.learning_rate, optimizer_dict=optimizer_dict)
    else:
        param_groups = [
            dict(params=nodecay_params, weight_decay=0.0),
            dict(params=decay_params, weight_decay=training_args.weight_decay),
            dict(params=apollo_params, weight_decay=training_args.weight_decay, **apollo_kwargs),
        ]
        optimizer = optim_class(param_groups, **optim_kwargs)

    logger.info_rank0(f"Using APOLLO optimizer with args: {apollo_kwargs}.")
    return optimizer