def _fa4_common_support_error(
    query: torch.Tensor,
    tensors: tuple[torch.Tensor, ...],
    cum_seq_q: torch.Tensor | None,
    require_fp32: tuple[tuple[str, torch.Tensor], ...] = (),
) -> str | None:
    if not all(t.is_cuda for t in tensors):
        return "inputs must be CUDA tensors"
    if len({t.device for t in tensors}) != 1:
        return "inputs must share device"
    if query.dtype not in (torch.float16, torch.bfloat16):
        return "query dtype must be float16 or bfloat16"
    for name, tensor in require_fp32:
        if tensor.dtype != torch.float32:
            return f"{name} dtype must be float32"
    if cum_seq_q is None and query.dim() != 4:
        return "dense query must be 4D"
    if cum_seq_q is not None and query.dim() != 3:
        return "ragged query must be 3D"
    if not torch.cuda.is_available():
        return "CUDA not available"
    if _get_device_major(query.device) not in (9, 10):
        return "FA4 requires compute capability 9.0 or 10.0"
    return None