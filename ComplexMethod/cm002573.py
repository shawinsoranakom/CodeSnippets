def get_total_byte_count(
    model: PreTrainedModel, accelerator_device_map: dict, hf_quantizer: HfQuantizer | None = None
):
    """
    This utility function calculates the total bytes count needed to load the model on each device.
    This is useful for caching_allocator_warmup as we want to know how much cache we need to pre-allocate.
    """

    total_byte_count = defaultdict(lambda: 0)
    tied_param_names = model.all_tied_weights_keys.keys()
    tp_plan = model._tp_plan if torch.distributed.is_available() and torch.distributed.is_initialized() else []

    for param_name, device in accelerator_device_map.items():
        # Skip if the parameter has already been accounted for (tied weights)
        if param_name in tied_param_names:
            continue

        param = model.get_parameter_or_buffer(param_name)

        if hf_quantizer is not None:
            dtype_size = hf_quantizer.param_element_size(model, param_name, param)
        else:
            dtype_size = param.element_size()

        param_byte_count = param.numel() * dtype_size

        if len(tp_plan) > 0:
            is_part_of_plan = _get_parameter_tp_plan(param_name, tp_plan, is_weight=True) is not None
            param_byte_count //= torch.distributed.get_world_size() if is_part_of_plan else 1

        total_byte_count[device] += param_byte_count
    return total_byte_count