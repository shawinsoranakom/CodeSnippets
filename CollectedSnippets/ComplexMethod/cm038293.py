def _fp8_linear_may_use_deep_gemm(module: torch.nn.Module) -> bool:
    """
    Return True if the input module/layer could be processed with DeepGEMM.
    """

    # FIXME: this logic is brittle and incorrect - since we
    # could use DeepGEMM with for than just Fp8LinearMethod
    block_size = get_mk_alignment_for_contiguous_layout()[0]
    if not (
        isinstance(module, LinearBase)
        and isinstance(module.quant_method, Fp8LinearMethod)
        and not isinstance(module.quant_method, Mxfp8OnlineLinearMethod)
        and getattr(module.quant_method, "block_quant", False)
        and not getattr(module.quant_method, "use_marlin", True)
    ):
        return False

    w, _, block_sizes = _extract_data_from_linear_base_module(module)
    return (
        block_sizes == get_mk_alignment_for_contiguous_layout()
        and w.ndim == 2
        and w.shape[0] % block_size == 0
        and w.shape[1] % block_size == 0
    )