def shard_and_distribute_module(
    model, param, empty_param, parameter_name, param_casting_dtype, is_contiguous, rank, device_mesh
):
    r"""
    This function is called in `from_pretrained` when loading a model's checkpoints.
    It receives the pointer to the parameter (or the parameter itself) and takes care of "sharding".
    All process run this function, so they just load the partition of the tensor that they require.

    Main uses cases:
    - column / rowise parallelism, you just shard all the weights of the layer (weight and bias)
    - packed layers: you slice the weights, then shard like above
    - custom operation:
        - you want to add an all-gather at the end of a local layer.
        - you want to have a layer that is isolated from the rest of the world (because torch.DTensor does not work well with `.view` for instance)

    """
    param_name, param_type = parameter_name.rsplit(".", 1) if "." in parameter_name else parameter_name
    tp_plan = model.tp_plan or {}
    module_to_tp = model.get_submodule(param_name)
    rank = int(rank)
    current_shard_plan = _get_parameter_tp_plan(parameter_name, tp_plan)

    if dist.get_rank() == 0:
        if current_shard_plan is None:
            logger.info(f"Tensor sharding plan for {param_name} not found, using default 'replicate' plan.")
        else:
            logger.info(f"Tensor sharding plan for {param_name}: {current_shard_plan}")

    if current_shard_plan is not None:
        try:
            tp_layer = ALL_PARALLEL_STYLES[current_shard_plan]
            tp_layer.empty_param = empty_param
            tp_layer.device_mesh = device_mesh
            tp_layer.rank = rank
            param = tp_layer.shard_tensor(param, tensor_idx=None, dtype=param_casting_dtype, device=rank)
            if is_contiguous:
                param = param.contiguous()
        except NotImplementedError as e:
            print(
                f"Trying to prepare {parameter_name}, but it's not supported. Corresponding module: {module_to_tp} Fix it's TP plan, current layer: {tp_layer} : {e}"
            )
    else:
        param = param[:].to(param_casting_dtype)

    # SUPER IMPORTANT we have to use setattr
    # otherwise loading is crazy slow
    if not isinstance(param, torch.nn.Parameter):
        param = torch.nn.Parameter(param, requires_grad=empty_param.is_floating_point())
    setattr(module_to_tp, param_type, param)
    tp_layer.update_module_attributes(module_to_tp)
    return param