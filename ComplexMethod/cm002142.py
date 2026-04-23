def _replace_with_int8_symmetric_linear(
    model,
    modules_to_not_convert=None,
    current_key_name=None,
    quantization_config=None,
    has_been_replaced=False,
    pre_quantized=False,
):
    """
    Recursively replaces nn.Linear modules with Int8SymmetricLinear modules.
    """
    if current_key_name is None:
        current_key_name = []

    for name, module in model.named_children():
        current_key_name.append(name)

        if (isinstance(module, nn.Linear)) and name not in modules_to_not_convert:
            # Check if the current key is not in the `modules_to_not_convert`
            current_key_name_str = ".".join(current_key_name)
            if not any(
                (key + "." in current_key_name_str) or (key == current_key_name_str) for key in modules_to_not_convert
            ):
                with init_empty_weights(include_buffers=True):
                    in_features = module.in_features
                    out_features = module.out_features
                    model._modules[name] = Int8SymmetricLinear(
                        in_features, out_features, module.bias is not None, dtype=module.weight.dtype
                    )
                    has_been_replaced = True
                    model._modules[name].requires_grad_(False)

        if len(list(module.children())) > 0:
            _, has_been_replaced = _replace_with_int8_symmetric_linear(
                module,
                modules_to_not_convert,
                current_key_name,
                quantization_config,
                has_been_replaced=has_been_replaced,
                pre_quantized=pre_quantized,
            )
        # Remove the last key for recursion
        current_key_name.pop(-1)
    return model, has_been_replaced