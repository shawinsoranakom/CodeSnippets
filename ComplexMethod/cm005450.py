def replace_with_bnb_linear(
    model: torch.nn.Module,
    modules_to_not_convert: list[str] | None = None,
    quantization_config=None,
    pre_quantized=False,
):
    """
    A helper function to replace all `torch.nn.Linear` modules by bnb modules from the `bitsandbytes` library.

    Args:
        model (`torch.nn.Module`):
            The model to convert, can be any `torch.nn.Module` instance.
        modules_to_not_convert (`list[str]`, defaults to `None`):
            A list of nn.Linear weights to not convert. If a parameter path is in the list (e.g. `lm_head.weight`), the corresponding module will not be
            converted.
        quantization_config (`BitsAndBytesConfig`):
            The quantization config object that contains the quantization parameters.
        pre_quantized (`book`, defaults to `False`):
            Whether the model is pre-quantized or not
    """
    has_been_replaced = False
    # we need this to correctly materialize the weights during quantization
    for module_name, module in model.named_modules():
        if not should_convert_module(module_name, modules_to_not_convert):
            continue
        new_module = None
        with torch.device("meta"):
            if isinstance(module, Conv1D) or type(module) is nn.Linear:
                if isinstance(module, Conv1D):
                    in_features, out_features = module.weight.shape
                else:
                    in_features = module.in_features
                    out_features = module.out_features
                if quantization_config.quantization_method() == "llm_int8":
                    new_module = bnb.nn.Linear8bitLt(
                        in_features,
                        out_features,
                        module.bias is not None,
                        has_fp16_weights=quantization_config.llm_int8_has_fp16_weight,
                        threshold=quantization_config.llm_int8_threshold,
                    )
                    if pre_quantized:
                        # this is kind of an edge case when supporting both loading and quantization ...
                        # we need to set the right dtype as we cast the checkpoint with the dtype of the meta model
                        new_module.weight.data = new_module.weight.data.to(dtype=torch.int8)
                else:
                    new_module = bnb.nn.Linear4bit(
                        in_features,
                        out_features,
                        module.bias is not None,
                        quantization_config.bnb_4bit_compute_dtype,
                        compress_statistics=quantization_config.bnb_4bit_use_double_quant,
                        quant_type=quantization_config.bnb_4bit_quant_type,
                        quant_storage=quantization_config.bnb_4bit_quant_storage,
                    )
                    if pre_quantized:
                        # same here
                        new_module.weight.data = new_module.weight.data.to(
                            dtype=quantization_config.bnb_4bit_quant_storage
                        )
                if new_module is not None:
                    # Store the module class in case we need to transpose the weight later
                    new_module.source_cls = type(module)
                    # Force requires grad to False to avoid unexpected errors
                    new_module.requires_grad_(False)
                    model.set_submodule(module_name, new_module)
                    has_been_replaced = True

    if not has_been_replaced:
        logger.warning(
            "You are loading your model using eetq but no linear modules were found in your model."
            " Please double check your model architecture, or submit an issue on github if you think this is"
            " a bug."
        )
    return model