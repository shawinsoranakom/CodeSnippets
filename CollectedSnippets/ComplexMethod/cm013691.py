def _fa4_forward_support_error(
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    dropout_p: float,
    return_debug_mask: bool,
    alibi_slopes: torch.Tensor | None,
    seqused_k: torch.Tensor | None,
    cum_seq_q: torch.Tensor | None,
    block_table: torch.Tensor | None = None,
    num_splits: int | None = None,
) -> str | None:
    if dropout_p != 0.0:
        return "dropout_p must be 0"
    if return_debug_mask:
        return "return_debug_mask must be False"
    if alibi_slopes is not None:
        return "alibi_slopes not supported"
    if seqused_k is not None:
        if seqused_k.dtype != torch.int32:
            return "seqused_k must be int32"
        if not seqused_k.is_cuda:
            return "seqused_k must be CUDA"
    major = _get_device_major(query.device)
    if block_table is not None and major != 10:
        return f"paged KV (block_table) not supported on SM {major}0"
    if num_splits is not None and num_splits > 1 and major != 10:
        return f"SplitKV (num_splits > 1) not supported on SM {major}0"
    error = _fa4_common_support_error(
        query,
        (query, key, value),
        cum_seq_q,
    )
    if error is not None:
        if error == "inputs must share device":
            return "query, key, value must be on same device"
        return error
    return None