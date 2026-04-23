def accelerate_dispatch(model, hf_quantizer, device_map, offload_folder, offload_index, offload_buffers):
    device_map_kwargs = {
        "device_map": device_map,
        "offload_dir": offload_folder,
        "offload_index": offload_index,
        "offload_buffers": offload_buffers,
    }
    if "skip_keys" in inspect.signature(dispatch_model).parameters:
        device_map_kwargs["skip_keys"] = model._skip_keys_device_placement
    # For HQQ method we force-set the hooks for single GPU envs
    if (
        "force_hooks" in inspect.signature(dispatch_model).parameters
        and hf_quantizer is not None
        and hf_quantizer.quantization_config.quant_method == QuantizationMethod.HQQ
    ):
        device_map_kwargs["force_hooks"] = True
    if (
        hf_quantizer is not None
        and hf_quantizer.quantization_config.quant_method == QuantizationMethod.FBGEMM_FP8
        and isinstance(device_map, dict)
        and ("cpu" in device_map.values() or "disk" in device_map.values())
    ):
        device_map_kwargs["offload_buffers"] = True

    if not is_fsdp_enabled() and not is_deepspeed_zero3_enabled():
        dispatch_model(model, **device_map_kwargs)