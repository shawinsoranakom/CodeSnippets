def _fa3_common_support_error(
    query: torch.Tensor,
    tensors: tuple[torch.Tensor, ...],
    dropout_p: float,
    cum_seq_q: torch.Tensor | None,
    q_descale: torch.Tensor | None,
    k_descale: torch.Tensor | None,
    v_descale: torch.Tensor | None,
) -> str | None:
    if dropout_p != 0.0:
        return "dropout_p must be 0"

    if not all(t.is_cuda for t in tensors):
        return "inputs must be CUDA tensors"
    if len({t.device for t in tensors}) != 1:
        return "inputs must share device"
    if query.dtype == torch.float8_e4m3fn and (
        q_descale is None or k_descale is None or v_descale is None
    ):
        warnings.warn(
            "When using SDPA with fp8, descale tensor should always be used"
            " for accurate dequantization. Please use "
            "_scaled_dot_product_attention_quantized and "
            "provide the descale tensors.",
            UserWarning,
        )
    if cum_seq_q is None and query.dim() != 4:
        return "dense query must be 4D"
    if cum_seq_q is not None and query.dim() != 3:
        return "ragged query must be 3D"
    if not torch.cuda.is_available():
        return "CUDA not available"
    if _get_device_major(query.device) != 9:
        return "FA3 requires compute capability 9.0"
    return None