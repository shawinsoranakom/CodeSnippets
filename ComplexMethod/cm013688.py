def _fa3_backward_support_error(
    grad_out: torch.Tensor,
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    out: torch.Tensor,
    logsumexp: torch.Tensor,
    dropout_p: float,
    cum_seq_q: torch.Tensor | None,
    window_size_left: int | None,
    window_size_right: int | None,
) -> str | None:
    # FA3 backward ONLY supports fp16/bf16, NOT fp8
    if query.dtype == torch.float8_e4m3fn:
        return (
            "FA3 backward does not support fp8 - use inference only (torch.no_grad())"
        )
    if logsumexp.dtype != torch.float32:
        return "logsumexp dtype must be float32"
    supported_dtypes = (torch.float16, torch.bfloat16)
    if not all(t.dtype in supported_dtypes for t in {grad_out, query, key, value, out}):
        return f"inputs must be one of {supported_dtypes}"
    if len({t.dtype for t in {grad_out, query, key, value, out}}) != 1:
        return "all inputs must have the same dtype"
    error = _fa3_common_support_error(
        query,
        (grad_out, query, key, value, out, logsumexp),
        dropout_p,
        cum_seq_q,
        None,
        None,
        None,
    )
    if error is not None:
        return error
    return None