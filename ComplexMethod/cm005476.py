def distribute_model(model, tp_plan, distributed_config, device_mesh, tp_size):
    """Distribute a model according to the TP plan."""
    model._tp_size = tp_size
    model._device_mesh = device_mesh
    if distributed_config is not None:
        if isinstance(distributed_config, dict):
            distributed_config = DistributedConfig.from_dict(distributed_config)
        model.config.distributed_config = distributed_config
    # Set the new requested tp_plan on the model
    if isinstance(tp_plan, dict):
        model.tp_plan = tp_plan
    model_plan = model.tp_plan
    if model_plan is not None and _torch_distributed_available:
        for v in model_plan.values():
            if v not in ALL_PARALLEL_STYLES:
                raise ValueError(f"Unsupported tensor parallel style {v}. Supported styles are {ALL_PARALLEL_STYLES}")
        for name, module in model.named_modules():
            if not getattr(module, "_is_hooked", False):
                plan = _get_parameter_tp_plan(parameter_name=name, tp_plan=model_plan, is_weight=False)
                add_tensor_parallel_hooks_to_module(
                    model,
                    module,
                    plan,
                    name,
                    device_mesh,
                )
            module._is_hooked = True
    return model