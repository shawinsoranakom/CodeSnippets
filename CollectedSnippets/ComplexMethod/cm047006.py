def get_lora_parameters(proj):
    """
    Return a 5-tuple of (weight, weight quant_state, lora A, lora B, and lora scale).
    If QAT is enabled, additionally fake quantize the base layer and lora weights.
    """
    # For DPO or disabled adapters
    base_layer = getattr(
        proj, "base_layer", proj
    )  # (proj.base_layer if hasattr(proj, "base_layer") else proj)
    W = base_layer.weight

    # Optionally apply fake quantization to base layer weights for QAT
    if hasattr(base_layer, "weight_fake_quantizer"):
        weight_fake_quantizer = getattr(base_layer, "weight_fake_quantizer", None)
        if weight_fake_quantizer is not None:
            W = weight_fake_quantizer(W)

    # Get quant state for 4bit or FP8
    W_quant = getattr(W, "quant_state", None)
    if W_quant is None:
        W_quant = getattr(base_layer, "weight_scale_inv", None)
        if W_quant is None:
            W_quant = getattr(base_layer, "weight_scale", None)

    if getattr(base_layer, "quant_method", None) == "fp8":
        # we need to somehow store and pass this information :)
        W.block_size = getattr(base_layer, "block_size", [128, 128])
        W_quant.block_size = W.block_size

    # if not hasattr(proj, "disable_adapters") or proj.disable_adapters or proj.merged:
    if getattr(proj, "disable_adapters", True) or proj.merged:
        return W, W_quant, None, None, None

    adapter = getattr(proj, "active_adapters", None)
    if adapter is None:
        adapter = getattr(proj, "active_adapter", ("default"))
    adapter = adapter[0]

    # Optionally apply fake quantization to lora weights for QAT
    lora_A_linear = proj.lora_A[adapter]
    lora_B_linear = proj.lora_B[adapter]
    A = lora_A_linear.weight
    B = lora_B_linear.weight
    if hasattr(lora_A_linear, "weight_fake_quantizer"):
        lora_A_fake_quantizer = getattr(lora_A_linear, "weight_fake_quantizer", None)
        if lora_A_fake_quantizer is not None:
            A = lora_A_fake_quantizer(A)
    if hasattr(lora_B_linear, "weight_fake_quantizer"):
        lora_B_fake_quantizer = getattr(lora_B_linear, "weight_fake_quantizer", None)
        if lora_B_fake_quantizer is not None:
            B = lora_B_fake_quantizer(B)

    return (
        W,
        W_quant,
        A,
        B,
        proj.scaling[adapter],
    )