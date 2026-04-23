def bmm_batch_invariant(a, b, *, out=None):
    # Batched matrix multiply: (B, M, K) x (B, K, N) -> (B, M, N)
    if not (a.ndim == 3 and b.ndim == 3):
        raise ValueError(
            f"bmm_batch_invariant expects 3D tensors, "
            f"got shapes {a.shape} and {b.shape}"
        )

    if a.shape[0] != b.shape[0]:
        raise ValueError(
            f"Batch dimensions of tensors must match, "
            f"but got {a.shape[0]} and {b.shape[0]}."
        )
    if a.shape[2] != b.shape[1]:
        raise ValueError(
            f"Incompatible inner dimensions for matmul: got {a.shape} and {b.shape}."
        )
    if a.dtype != b.dtype:
        raise ValueError(f"Incompatible dtypes: got {a.dtype} and {b.dtype}.")

    B, M, K = a.shape
    _, _, N = b.shape
    dtype = a.dtype

    if out is None:
        c = torch.empty((B, M, N), device=a.device, dtype=dtype)
    else:
        assert out.shape == (B, M, N), "out tensor has incorrect shape"
        assert out.dtype == dtype and out.device == a.device, "out tensor mismatch"
        c = out

    configs = {
        torch.bfloat16: {
            "BLOCK_SIZE_M": 128,
            "BLOCK_SIZE_N": 128,
            "BLOCK_SIZE_K": 64,
            "num_stages": 3,
            "num_warps": 8,
        },
        torch.float16: {
            "BLOCK_SIZE_M": 128,
            "BLOCK_SIZE_N": _fp16_block_size_n,
            "BLOCK_SIZE_K": 64,
            "num_stages": 3,
            "num_warps": 8,
        },
        torch.float32: {
            "BLOCK_SIZE_M": 128,
            "BLOCK_SIZE_N": 128,
            "BLOCK_SIZE_K": 32,
            "num_stages": 3,
            "num_warps": 8,
        },
    }

    cfg = configs[dtype]
    # grid = (B, num_tiles_per_matrix)
    grid = (
        B,
        triton.cdiv(M, cfg["BLOCK_SIZE_M"]) * triton.cdiv(N, cfg["BLOCK_SIZE_N"]),
    )

    bmm_kernel[grid](
        a,
        b,
        c,
        B,
        M,
        N,
        K,
        a.stride(0),
        a.stride(1),
        a.stride(2),
        b.stride(0),
        b.stride(1),
        b.stride(2),
        c.stride(0),
        c.stride(1),
        c.stride(2),
        A_LARGE=a.numel() > 2**31,
        B_LARGE=b.numel() > 2**31,
        C_LARGE=c.numel() > 2**31,
        **cfg,
    )

    return c