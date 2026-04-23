def triton_w4a16_gemm(
    a: torch.Tensor,  # [M, K] fp16/bf16
    b_q: torch.Tensor,  # [K, N//8] int32
    scales: torch.Tensor,  # [K//G, N] fp16/bf16
    qzeros: torch.Tensor | None,  # [K//G, N//8] int32, or None
    group_size: int,
    zp_bias: int = 8,  # bias for uint4b8 when qzeros is None
) -> torch.Tensor:
    """
    Fused W4A16 GEMM using GPTQ-packed int4 weights.

    Args:
        a:          Activation matrix [M, K], float16 or bfloat16.
        b_q:        Packed weight matrix [K, N//8], int32 (GPTQ sequential).
        scales:     Per-group scales [K//G, N], same dtype as a.
        qzeros:     Per-group packed zero points [K//G, N//8] int32, or None
                    for symmetric quantization (uses zp_bias instead).
        group_size: Quantization group size (resolved from -1 to K by caller).
        zp_bias:    Constant zero used when qzeros is None (default 8 for uint4b8).

    Returns:
        Output matrix [M, N], same dtype as a.
    """
    assert a.is_contiguous(), "Activation matrix must be contiguous"
    assert b_q.is_contiguous(), "Weight matrix must be contiguous"
    assert scales.is_contiguous(), "Scales must be contiguous"

    M, K = a.shape
    N = b_q.shape[1] * 8

    assert b_q.shape == (K, N // 8), (
        f"b_q shape mismatch: {b_q.shape} vs ({K}, {N // 8})"
    )
    assert scales.shape == (K // group_size, N), (
        f"scales shape mismatch: {scales.shape} vs ({K // group_size}, {N})"
    )
    if qzeros is not None:
        assert qzeros.shape == (K // group_size, N // 8), (
            f"qzeros shape mismatch: {qzeros.shape}"
        )

    c = torch.empty((M, N), dtype=a.dtype, device=a.device)

    has_zp = qzeros is not None
    # Provide a dummy pointer when HAS_ZP=False (Triton requires a valid ptr)
    zeros_ptr = qzeros if has_zp else b_q

    if current_platform.is_rocm():
        from vllm.platforms.rocm import on_gfx1x

        if on_gfx1x():
            # Tuned for RDNA 3.5 (gfx1151, 40 CUs, 32-wide wavefronts).
            if M <= 32:
                BLOCK_M, BLOCK_N, BLOCK_K = 32, 32, 64
            elif M <= 64:
                BLOCK_M, BLOCK_N, BLOCK_K = 64, 64, 32
            else:
                BLOCK_M, BLOCK_N, BLOCK_K = 128, 32, 64
        else:
            # Tuned for MI300 (gfx942, 304 CUs, 64-wide wavefronts).
            if M <= 32:
                BLOCK_M, BLOCK_N, BLOCK_K = 32, 64, 32
            elif M <= 64:
                BLOCK_M, BLOCK_N, BLOCK_K = 64, 64, 32
            else:
                BLOCK_M, BLOCK_N, BLOCK_K = 128, 128, 32
    else:
        if M <= 32:
            BLOCK_M, BLOCK_N, BLOCK_K = 32, 64, 32
        elif M <= 64:
            BLOCK_M, BLOCK_N, BLOCK_K = 64, 64, 32
        else:
            BLOCK_M, BLOCK_N, BLOCK_K = 128, 128, 32

    # The kernel loads scales/zeros for a single group per BLOCK_K tile
    # (one g_idx per iteration). If BLOCK_K > group_size, rows at the tail
    # of the tile dequantize with the wrong group's scales, silently
    # corrupting the output. Clamp BLOCK_K to group_size to keep one
    # scale group per tile.
    if group_size < BLOCK_K:
        BLOCK_K = group_size

    grid = (triton.cdiv(M, BLOCK_M), triton.cdiv(N, BLOCK_N))

    triton_w4a16_gemm_kernel[grid](
        a,
        b_q,
        scales,
        zeros_ptr,
        c,
        M,
        N,
        K,
        a.stride(0),
        a.stride(1),
        b_q.stride(0),
        b_q.stride(1),
        c.stride(0),
        c.stride(1),
        group_size=group_size,
        HAS_ZP=has_zp,
        ZP_BIAS=zp_bias,
        BLOCK_M=BLOCK_M,
        BLOCK_N=BLOCK_N,
        BLOCK_K=BLOCK_K,
    )
    return c