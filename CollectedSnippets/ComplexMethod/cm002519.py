def set_param_for_module(
    model: PreTrainedModel,
    target_name: str,
    param_value: torch.Tensor,
    loading_info: LoadStateDictInfo,
    distributed_operation: TensorParallelLayer | None,
    hf_quantizer: HfQuantizer,
):
    module_path, _, param_name = target_name.rpartition(".")
    module_obj = model.get_submodule(module_path) if module_path else model

    if param_name == torch.nn.modules.module._EXTRA_STATE_KEY_SUFFIX:
        module_obj.set_extra_state(param_value)
        loading_info.missing_keys.discard(target_name)
        return

    ref = getattr(module_obj, param_name)
    if ref is None:
        loading_info.unexpected_keys.add(target_name)
    else:
        if not isinstance(param_value, torch.nn.Parameter):
            if param_name not in module_obj._buffers:
                param_value = torch.nn.Parameter(param_value, requires_grad=param_value.is_floating_point())

        # Remove from missing keys (it's either mismatched, or all good)
        loading_info.missing_keys.discard(target_name)

        # Determine expected shape: for TP, use sharded shape; otherwise, use full shape
        if distributed_operation is not None:
            expected_shape = torch.Size(distributed_operation.get_expected_sharded_shape(ref.shape))
        else:
            expected_shape = ref.shape

        if ref is not None and param_value.shape != expected_shape and hf_quantizer is None:
            loading_info.mismatched_keys.add((target_name, param_value.shape, expected_shape))
        else:
            # super important otherwise _init_weight will re-init the param
            param_value._is_hf_initialized = True
            setattr(module_obj, param_name, param_value)
            if distributed_operation is not None:
                distributed_operation.update_module_attributes(module_obj)