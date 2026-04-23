def _valid_deep_gemm(
    hidden_states: torch.Tensor, w1: torch.Tensor, w2: torch.Tensor
) -> bool:
    """
    Check if the given problem size is supported by the DeepGemm grouped
    gemm kernel.  All of M, N, K and the quantization block_shape must be
    aligned by `dg.get_m_alignment_for_contiguous_layout()`.
    """
    if not has_deep_gemm():
        logger.debug_once("DeepGemm disabled: deep_gemm not available.")
        return False

    M = hidden_states.size(0)
    _, K, N = w2.size()

    align = get_mk_alignment_for_contiguous_layout()[0]

    if not _valid_deep_gemm_shape(M, N, K):
        logger.debug_once(
            "DeepGemm disabled due to unaligned problem size. "
            "M: %s, N: %s, K: %s. M should >= %s "
            "and N and K must be multiples of %s. "
            "This is not an error and we will fall back to triton.",
            M,
            N,
            K,
            align,
            align,
        )
        return False
    elif N <= 512:
        logger.debug_once(
            "DeepGemm disabled for N <= 512. M: %s, N: %s, K: %s. "
            "This means we will fallback to triton "
            "for this specific shape for further speed up.",
            M,
            N,
            K,
        )
        return False

    if w1.dtype != torch.float8_e4m3fn or w2.dtype != torch.float8_e4m3fn:
        logger.debug_once(
            "DeepGemm disabled: invalid weight dtype(s). w1.dtype: %s, w2.dtype: %s",
            w1.dtype,
            w2.dtype,
        )
        return False

    if (
        not hidden_states.is_contiguous()
        or not w1.is_contiguous()
        or not w2.is_contiguous()
    ):
        logger.debug_once(
            "DeepGemm disabled: weights or activations not contiguous. "
            "hidden_states.is_contiguous(): %s, w1.is_contiguous(): %s, "
            "w2.is_contiguous(): %s",
            hidden_states.is_contiguous(),
            w1.is_contiguous(),
            w2.is_contiguous(),
        )
        return False

    return True