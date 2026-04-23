def get_hf_quantizer(config, quantization_config, device_map, weights_only, user_agent):
    pre_quantized = hasattr(config, "quantization_config")
    if pre_quantized and not AutoHfQuantizer.supports_quant_method(config.quantization_config):
        pre_quantized = False

    if pre_quantized or quantization_config is not None:
        if pre_quantized:
            config.quantization_config = AutoHfQuantizer.merge_quantization_configs(
                config.quantization_config, quantization_config
            )
        else:
            config.quantization_config = quantization_config

        hf_quantizer = AutoHfQuantizer.from_config(
            config.quantization_config,
            pre_quantized=pre_quantized,
        )
    else:
        hf_quantizer = None

    if hf_quantizer is not None:
        hf_quantizer.validate_environment(
            device_map=device_map,
            weights_only=weights_only,
        )
        device_map = hf_quantizer.update_device_map(device_map)
        config = hf_quantizer.update_tp_plan(config)
        config = hf_quantizer.update_ep_plan(config)

        # In order to ensure popular quantization methods are supported. Can be disable with `disable_telemetry`
        if not getattr(hf_quantizer.quantization_config, "dequantize", False):
            quant_method = hf_quantizer.quantization_config.quant_method
            user_agent["quant"] = getattr(quant_method, "value", quant_method)
    return hf_quantizer, config, device_map