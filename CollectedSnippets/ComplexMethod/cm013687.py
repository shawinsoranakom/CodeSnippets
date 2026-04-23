def _fa3_forward_support_error(
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    dropout_p: float,
    return_debug_mask: bool,
    alibi_slopes: torch.Tensor | None,
    seqused_k: torch.Tensor | None,
    cum_seq_q: torch.Tensor | None,
    q_descale: torch.Tensor | None,
    k_descale: torch.Tensor | None,
    v_descale: torch.Tensor | None,
) -> str | None:
    if return_debug_mask:
        return "return_debug_mask must be False"
    if alibi_slopes is not None:
        return "alibi_slopes not supported"
    if seqused_k is not None:
        if seqused_k.dtype != torch.int32:
            return "seqused_k must be int32"
        if not seqused_k.is_cuda:
            return "seqused_k must be CUDA"
    supported_dtypes = (torch.float8_e4m3fn, torch.float16, torch.bfloat16)
    if not all(t.dtype in supported_dtypes for t in {query, key, value}):
        return f"inputs must be one of {supported_dtypes}"
    if len({t.dtype for t in {query, key, value}}) != 1:
        return "all inputs must have the same dtype"
    error = _fa3_common_support_error(
        query,
        (query, key, value),
        dropout_p,
        cum_seq_q,
        q_descale,
        k_descale,
        v_descale,
    )
    if error is not None:
        if error == "inputs must share device":
            return "query, key, value must be on same device"
        return error
    return None