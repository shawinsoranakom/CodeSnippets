def get_and_maybe_dequant_weights(
    layer: "LinearBase", out_dtype: torch.dtype = torch.float32
):
    """Return layer's unquantized weights in [out, in] layout"""
    from vllm.model_executor.layers.linear import UnquantizedLinearMethod
    from vllm.model_executor.layers.quantization.fp8 import Fp8LinearMethod

    # LoRA linear wrappers store quantization metadata on `base_layer`.
    # Unwrap here so callers can pass either a raw linear layer or its LoRA
    # wrapper without special-casing.
    while hasattr(layer, "base_layer") and hasattr(layer.base_layer, "quant_method"):
        layer = layer.base_layer

    weight = get_attribute_fallback(layer, ["weight", "qweight", "weight_packed"])

    # Unquantized layer: just return base weights
    if layer.quant_method is None or isinstance(
        layer.quant_method, UnquantizedLinearMethod
    ):
        return weight.to(out_dtype)

    # Simple Fp8 case: rescale with tensor or block weight scales
    if (
        isinstance(layer.quant_method, Fp8LinearMethod)
        and not layer.quant_method.use_marlin
        # DeepGEMM transforms the scales using `transform_sf_into_required_layout` into
        # a layout that is not compatible with `scaled_dequantize`.
        and not layer.quant_method.use_deep_gemm
    ):
        weight_scales = get_attribute_fallback(
            layer, ["weight_scale", "weight_scale_inv"]
        )
        dequant_weights = scaled_dequantize(
            weight,
            weight_scales,
            group_shape=layer.weight_block_size,
            out_dtype=out_dtype,
        )
        # per-tensor scaling stores weights in [in, out] layout
        if not layer.quant_method.block_quant:
            dequant_weights = dequant_weights.T
        return dequant_weights

    # NOTE: Most generic base case
    # - Call the layer with identity matrix which returns unquantized weights.
    # - Must be used with extra care when dealing with static activation quantization:
    #   quantizing 1.0 may lead to over/underflows
    # - Should only be used offline, since it's O(N^3)
    assert hasattr(layer, "input_size_per_partition")
    eye = torch.eye(
        layer.input_size_per_partition,
        dtype=out_dtype,
        device=weight.device,
    )
    dequant_weights = layer.quant_method.apply(layer, eye, bias=None).to(out_dtype)
    return dequant_weights.T