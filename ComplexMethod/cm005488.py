def replace_with_sinq_linear(
    model: torch.nn.Module,
    modules_to_not_convert: list[str] | None = None,
    quant_config: dict | None = None,
    compute_dtype: torch.dtype = None,
    device: str = "cuda:0",
    pre_quantized: bool = False,
) -> torch.nn.Module:
    """
    Replace nn.Linear modules with empty SINQLinear modules.

    Args:
        model: The model to modify
        modules_to_not_convert: List of module names to skip
        quant_config: SINQ quantization config dict (None for pre-quantized models)
        compute_dtype: Computation dtype for the quantized layers
        device: Device string for the quantized layers
        pre_quantized: Whether loading a pre-quantized checkpoint

    Returns:
        The modified model with SINQLinear modules
    """
    from sinq.sinqlinear_hf import SINQLinear

    if modules_to_not_convert is None:
        modules_to_not_convert = []

    for full_name, module in list(model.named_modules()):
        if not isinstance(module, nn.Linear):
            continue
        if not should_convert_module(full_name, modules_to_not_convert):
            continue

        parent_path, _, child_name = full_name.rpartition(".")
        parent = model.get_submodule(parent_path) if parent_path else model

        sinq_layer = SINQLinear(
            in_features=module.in_features if not pre_quantized else None,
            out_features=module.out_features if not pre_quantized else None,
            bias=(module.bias is not None) if not pre_quantized else False,
            quant_config=quant_config,
            compute_dtype=compute_dtype,
            device=device,
            use_unpack_kernel=True,
        )

        setattr(parent, child_name, sinq_layer)

    return model