def replace_with_bitnet_linear(model, modules_to_not_convert: list[str] | None = None, quantization_config=None):
    """
    Public method that replaces the linear layers of the given model with bitnet quantized layers.

    Args:
        model (`torch.nn.Module`):
            The model to convert, can be any `torch.nn.Module` instance.
        modules_to_not_convert (`list[str]`, *optional*, defaults to `None`):
            A list of nn.Linear weights to not convert. If a parameter path is in the list (e.g. `lm_head.weight`), the corresponding module will not be
            converted.
        quantization_config (`BitNetConfig`):
            The quantization config object that contains the quantization parameters.
    """

    has_been_replaced = False
    # we need this to correctly materialize the weights during quantization
    for module_name, module in model.named_modules():
        if not should_convert_module(module_name, modules_to_not_convert):
            continue
        with torch.device("meta"):
            if isinstance(module, nn.Linear):
                if quantization_config and quantization_config.linear_class == "autobitlinear":
                    new_module = AutoBitLinear(
                        in_features=module.in_features,
                        out_features=module.out_features,
                        bias=module.bias is not None,
                        device=module.weight.device,
                        dtype=module.weight.dtype,
                        online_quant=(quantization_config.quantization_mode == "online"),
                        use_rms_norm=quantization_config.use_rms_norm,
                        rms_norm_eps=quantization_config.rms_norm_eps,
                    )
                    if quantization_config.quantization_mode == "offline":
                        new_module.requires_grad_(False)
                else:
                    new_module = BitLinear(
                        in_features=module.in_features,
                        out_features=module.out_features,
                        bias=module.bias is not None,
                        device=module.weight.device,
                        dtype=module.weight.dtype,
                        use_rms_norm=quantization_config.use_rms_norm if quantization_config else False,
                        rms_norm_eps=quantization_config.rms_norm_eps if quantization_config else 1e-6,
                    )
                    new_module.requires_grad_(False)
                model.set_submodule(module_name, new_module)
                has_been_replaced = True

    if not has_been_replaced:
        logger.warning(
            "You are loading your model using bitnet but no linear modules were found in your model."
            " Please double check your model architecture, or submit an issue on github if you think this is"
            " a bug."
        )

    return model