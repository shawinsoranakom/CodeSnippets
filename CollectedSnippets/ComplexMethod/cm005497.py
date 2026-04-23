def replace_with_fbgemm_fp8_linear(
    model, modules_to_not_convert: list[str] | None = None, quantization_config=None, pre_quantized=False, tp_plan=None
):
    """
    A helper function to replace all `torch.nn.Linear` modules by `FbgemmFp8Linear` modules.
    This will enable running your models using high performance fp8 kernel from FBGEMM library.

    Parameters:
        model (`torch.nn.Module`):
            Input model or `torch.nn.Module` as the function is run recursively.
        modules_to_not_convert (`list[`str`]`, *optional*, defaults to `None`):
            Names of the modules to not convert. In practice we keep the `lm_head` in full precision for numerical stability reasons.
        quantization_config (`FbgemmFp8Config`):
            The quantization config object that contains the quantization parameters.
        pre_quantized (`book`, defaults to `False`):
            Whether the model is pre-quantized or not
    """
    global quantize_fp8_per_row
    quantize_fp8_per_row = get_quantize_fp8_per_row()

    has_been_replaced = False
    module_kwargs = {} if pre_quantized else {"dtype": None}

    for module_name, module in model.named_modules():
        if not should_convert_module(module_name, modules_to_not_convert):
            continue

        new_module = None
        with init_empty_weights(include_buffers=True):
            if module.__class__.__name__ == "Llama4TextExperts":
                # TODO: make sure tp works later
                # if tp_plan is not None:
                #     tp_key = re.sub(r"\d+", "*", f"{module_name}.down_proj_scale")
                #     tp_plan[tp_key] = None
                text_config = getattr(model.config, "text_config", model.config)
                new_module = FbgemmFp8Llama4TextExperts(text_config or model.config)
            elif isinstance(module, nn.Linear):
                new_module = FbgemmFp8Linear(
                    module.in_features,
                    module.out_features,
                    module.bias is not None,
                    **module_kwargs,
                )
                new_module.requires_grad_(False)

        if new_module is None:
            continue

        model.set_submodule(module_name, new_module)
        has_been_replaced = True

    if not has_been_replaced:
        logger.warning(
            "You are loading your model using FP8 quantization but no linear modules were found in your model."
            " Please double check your model architecture, or submit an issue on github if you think this is"
            " a bug."
        )

    return model