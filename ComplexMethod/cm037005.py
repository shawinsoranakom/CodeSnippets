def quantize_to_fp8_blockwise(
    tensor: torch.Tensor,
    group_n: int,
    group_k: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Quantize a 2D or 3D tensor to FP8 with block-wise scaling.

    For a 2D tensor (num_tokens, hidden_size):
        Blocks of size (1, group_k) ->
            scale shape (num_tokens, ceil(hidden_size/group_k))

    For a 3D tensor (num_loras, N, K):
        Blocks of size (group_n, group_k) ->
            scale shape (num_loras, ceil(N/group_n), ceil(K/group_k))
    """
    if tensor.ndim == 2:
        M, K = tensor.shape
        n_blocks_k = math.ceil(K / group_k)
        scale = torch.zeros(M, n_blocks_k, dtype=torch.float32, device=tensor.device)
        fp8_tensor = torch.zeros_like(tensor, dtype=FP8_DTYPE)
        for m in range(M):
            for bk in range(n_blocks_k):
                k_start = bk * group_k
                k_end = min(k_start + group_k, K)
                block = tensor[m, k_start:k_end].float()
                amax = block.abs().max().clamp(min=1e-12)
                s = (amax / FP8_MAX).to(torch.float32)
                scale[m, bk] = s
                fp8_tensor[m, k_start:k_end] = (
                    (block / s).clamp(FP8_MIN, FP8_MAX).to(FP8_DTYPE)
                )
        return fp8_tensor, scale
    elif tensor.ndim == 3:
        L, N, K = tensor.shape
        n_blocks_n = math.ceil(N / group_n)
        n_blocks_k = math.ceil(K / group_k)
        scale = torch.zeros(
            L, n_blocks_n, n_blocks_k, dtype=torch.float32, device=tensor.device
        )
        fp8_tensor = torch.zeros_like(tensor, dtype=FP8_DTYPE)
        for li in range(L):
            for bn in range(n_blocks_n):
                for bk in range(n_blocks_k):
                    n_start = bn * group_n
                    n_end = min(n_start + group_n, N)
                    k_start = bk * group_k
                    k_end = min(k_start + group_k, K)
                    block = tensor[li, n_start:n_end, k_start:k_end].float()
                    amax = block.abs().max().clamp(min=1e-12)
                    s = (amax / FP8_MAX).to(torch.float32)
                    scale[li, bn, bk] = s
                    fp8_tensor[li, n_start:n_end, k_start:k_end] = (
                        (block / s).clamp(FP8_MIN, FP8_MAX).to(FP8_DTYPE)
                    )
        return fp8_tensor, scale
    else:
        raise ValueError(f"Unsupported tensor ndim: {tensor.ndim}")