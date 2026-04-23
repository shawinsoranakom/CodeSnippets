def replace_with_mxfp4_linear(model, quantization_config=None, modules_to_not_convert: list[str] | None = None):
    """
    Public method that replaces the expert layers of the given model with mxfp4 quantized layers.

    Args:
        model (`torch.nn.Module`):
            The model to convert, can be any `torch.nn.Module` instance.
        quantization_config (`Mxfp4Config`, defaults to `None`):
            The quantization config object that contains the quantization parameters.
        modules_to_not_convert (`list`, *optional*, defaults to `None`):
            A list of modules to not convert. If a module name is in the list (e.g. `lm_head`), it will not be
            converted.
    """
    if quantization_config.dequantize:
        return model

    from .hub_kernels import get_kernel

    global triton_kernels_hub
    triton_kernels_hub = get_kernel("kernels-community/gpt-oss-triton-kernels")

    has_been_replaced = False
    for module_name, module in model.named_modules():
        if not should_convert_module(module_name, modules_to_not_convert):
            continue
        if module.__class__.__name__ == "GptOssExperts" and not quantization_config.dequantize:
            with torch.device("meta"):
                model.set_submodule(module_name, Mxfp4GptOssExperts(model.config))
                has_been_replaced = True
        if module.__class__.__name__ == "GptOssMLP" and not quantization_config.dequantize:
            from types import MethodType

            module.forward = MethodType(mlp_forward, module)

    if not has_been_replaced:
        logger.warning(
            "You are loading your model using mixed-precision FP4 quantization but no linear modules were found in your model."
            " Please double check your model architecture, or submit an issue on github if you think this is"
            " a bug."
        )

    return model