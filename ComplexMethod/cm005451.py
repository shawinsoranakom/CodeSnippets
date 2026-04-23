def dequantize_and_replace(model, quantization_config=None, dtype=None):
    """
    Converts a quantized model into its dequantized original version. The newly converted model will have
    some performance drop compared to the original model before quantization - use it only for specific usecases
    such as QLoRA adapters merging.

    Returns the converted model.
    """
    quant_method = quantization_config.quantization_method()

    target_cls = bnb.nn.Linear8bitLt if quant_method == "llm_int8" else bnb.nn.Linear4bit
    for module_name, module in model.named_modules():
        if isinstance(module, target_cls):
            with torch.device("meta"):
                bias = getattr(module, "bias", None)
                new_module = torch.nn.Linear(module.in_features, module.out_features, bias=bias is not None)
            state = module.state if quant_method == "llm_int8" else None
            new_module.weight = torch.nn.Parameter(dequantize_bnb_weight(module.weight, state))
            weight = dequantize_bnb_weight(module.weight, state)
            if dtype is None:
                logger.warning_once(
                    f"The modules are dequantized in {weight.dtype}. If you want to change the dtype, please specify `dtype` in `dequantize`. "
                )
            else:
                logger.warning_once(f"The modules are dequantized in {weight.dtype} and casted to {dtype}.")
                weight = weight.to(dtype)
            new_module.weight = torch.nn.Parameter(weight)
            if bias is not None:
                new_module.bias = bias
            if hasattr(module, "_hf_hook"):
                old_hook = module._hf_hook
                new_hook = _create_accelerate_new_hook(old_hook)
                remove_hook_from_module(module)
                add_hook_to_module(new_module, new_hook)
            new_module.to(module.weight.device)
            model.set_submodule(module_name, new_module)
            has_been_replaced = True

    if not has_been_replaced:
        logger.warning(
            "For some reason the model has not been properly dequantized. You might see unexpected behavior."
        )
    return model