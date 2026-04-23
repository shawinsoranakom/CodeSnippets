def replace_with_quanto_layers(
    model,
    quantization_config=None,
    modules_to_not_convert: list[str] | None = None,
):
    """
    Public method that recursively replaces the Linear layers of the given model with Quanto quantized layers.
    Returns the converted model and a boolean that indicates if the conversion has been successful or not.

    Args:
        model (`torch.nn.Module`):
            The model to convert, can be any `torch.nn.Module` instance.
        quantization_config (`QuantoConfig`, defaults to `None`):
            The quantization config object that contains the quantization parameters.
        modules_to_not_convert (`list`, *optional*, defaults to `None`):
            A list of modules to not convert. If a module name is in the list (e.g. `lm_head`), it will not be
            converted.
    """
    from optimum.quanto import QLayerNorm, QLinear, qfloat8, qint2, qint4, qint8

    w_mapping = {"float8": qfloat8, "int8": qint8, "int4": qint4, "int2": qint2}
    a_mapping = {None: None, "float8": qfloat8, "int8": qint8}

    has_been_replaced = False
    for module_name, module in model.named_modules():
        if not should_convert_module(module_name, modules_to_not_convert):
            continue
        with torch.device("meta"):
            new_module = None
            if isinstance(module, nn.Linear):
                new_module = QLinear(
                    in_features=module.in_features,
                    out_features=module.out_features,
                    bias=module.bias is not None,
                    dtype=module.weight.dtype,
                    weights=w_mapping[quantization_config.weights],
                    activations=a_mapping[quantization_config.activations],
                )
            elif isinstance(module, torch.nn.LayerNorm) and quantization_config.activations is not None:
                new_module = QLayerNorm(
                    module.normalized_shape,
                    module.eps,
                    module.elementwise_affine,
                    module.bias is not None,
                    activations=a_mapping[quantization_config.activations],
                )
            if new_module is not None:
                has_been_replaced = True
                model.set_submodule(module_name, new_module)

    if not has_been_replaced:
        logger.warning(
            "You are loading your model using quanto but no linear modules were found in your model."
            " Please double check your model architecture, or submit an issue on github if you think this is"
            " a bug."
        )

    return model