def dequantize_fp8_blockwise(
    fp8_tensor: torch.Tensor,
    scale: torch.Tensor,
    group_n: int,
    group_k: int,
    output_dtype: torch.dtype = torch.bfloat16,
) -> torch.Tensor:
    """Dequantize FP8 tensor with block-wise scale back to output_dtype."""
    if fp8_tensor.ndim == 2:
        M, K = fp8_tensor.shape
        out = torch.zeros(M, K, dtype=output_dtype, device=fp8_tensor.device)
        n_blocks_k = math.ceil(K / group_k)
        for m in range(M):
            for bk in range(n_blocks_k):
                k_start = bk * group_k
                k_end = min(k_start + group_k, K)
                out[m, k_start:k_end] = (
                    fp8_tensor[m, k_start:k_end].float() * scale[m, bk].float()
                ).to(output_dtype)
        return out
    elif fp8_tensor.ndim == 3:
        L, N, K = fp8_tensor.shape
        out = torch.zeros(L, N, K, dtype=output_dtype, device=fp8_tensor.device)
        n_blocks_n = math.ceil(N / group_n)
        n_blocks_k = math.ceil(K / group_k)
        for l_idx in range(L):
            for bn in range(n_blocks_n):
                for bk in range(n_blocks_k):
                    n_start = bn * group_n
                    n_end = min(n_start + group_n, N)
                    k_start = bk * group_k
                    k_end = min(k_start + group_k, K)
                    out[l_idx, n_start:n_end, k_start:k_end] = (
                        fp8_tensor[l_idx, n_start:n_end, k_start:k_end].float()
                        * scale[l_idx, bn, bk].float()
                    ).to(output_dtype)
        return out
    else:
        raise ValueError(f"Unsupported tensor ndim: {fp8_tensor.ndim}")