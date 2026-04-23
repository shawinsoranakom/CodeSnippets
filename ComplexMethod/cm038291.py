def _extract_data_from_linear_base_module(
    m: torch.nn.Module,
) -> tuple[torch.Tensor, torch.Tensor, list[int]]:
    """
    Extract weights, weight scales and quantization block sizes from the given
    LinearBase module.
    """
    assert isinstance(m, LinearBase)
    assert isinstance(m.quant_method, Fp8LinearMethod)
    assert m.quant_method.block_quant
    assert m.quant_method.quant_config is not None

    w = m.weight
    ws = m.weight_scale_inv if hasattr(m, "weight_scale_inv") else m.weight_scale
    quant_block_size = m.quant_method.quant_config.weight_block_size

    assert isinstance(w, torch.Tensor)
    assert isinstance(ws, torch.Tensor)
    assert quant_block_size is not None
    return (w, ws, quant_block_size)