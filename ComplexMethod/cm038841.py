def fp8_mm_k(
    a_ptr,
    b_ptr,
    a_scale_ptr,
    b_scale_ptr,
    ak_stride,
    bk_stride,
    a_scale_k_stride,
    b_scale_k_stride,
    offset_k,
    K: tl.constexpr,
    BLOCK_M: tl.constexpr,
    BLOCK_N: tl.constexpr,
    BLOCK_K: tl.constexpr,
    EVEN_K: tl.constexpr,
    SPLIT_K: tl.constexpr,
    group_k: tl.constexpr,
    group_n: tl.constexpr,
    use_fp8_w8a8: tl.constexpr,
    per_channel_quant: tl.constexpr,
    CAST_TYPE: tl.constexpr,
    b_dtype: tl.constexpr,
    USE_GDC: tl.constexpr,
    base_k,
):
    """
    FP8-compatible matrix multiplication kernel with quantization support.
    Given a_ptr and b_ptr, that identify the rows of A (m x k) and columns of
    B (k x n), iterate through the K dimension to compute the partial/complete
    matrix block product with proper dequantization.

    Args:
        a_ptr (tl.tensor): Array of pointers, identifying rows of A
            (FP8 or other dtype)
        b_ptr (tl.tensor): Array of pointers, identifying columns of B
            (FP8 dtype)
        a_scale_ptr (tl.tensor): Scale pointer for A matrix
            (per-token or block-wise)
        b_scale_ptr (tl.tensor): Scale pointer for B matrix
            (per-channel or block-wise)
        ak_stride (int): K dimension stride of the A matrix
        bk_stride (int): K dimension stride of the B matrix
        a_scale_k_stride (int): K dimension stride for A's block-wise scales
        b_scale_k_stride (int): K dimension stride for B's block-wise scales
        offset_k (int): Base offset along K dimension
        K: Length of the K dimension
        BLOCK_M: M dimension of the output block m x n
        BLOCK_N: N dimension of the output block m x n
        BLOCK_K: K dimension atom
        EVEN_K: True if the blocks of A and B can be loaded without masking
        SPLIT_K: Parameter signifying parallelism in the K dimension
        group_k: Block size for K dimension in block-wise quantization
        group_n: Block size for N dimension in block-wise quantization
        use_fp8_w8a8: Whether using FP8 W8A8 quantization
        per_channel_quant: Whether using per-channel quantization
        CAST_TYPE: if True, cast the values from the A matrix to the B
            matrix dtype.
        b_dtype: datatype of the B matrix
        USE_GDC: Whether to use PDL. True indicates use.
        base_k (int): Base offset along K dimension for current SPLIT_K group
    """
    accumulator = tl.zeros((BLOCK_M, BLOCK_N), dtype=tl.float32)

    # Step size along K for each iteration
    STEP_K = BLOCK_K * SPLIT_K

    # Total number of iterations (compile-time constant)
    num_iters = tl.cdiv(K, STEP_K)

    for k in range(num_iters):
        # Current iteration's global K offset
        iter_k = k * STEP_K + base_k
        block_end = iter_k + BLOCK_K

        # Skip iterations that are entirely past the K boundary
        if not EVEN_K and iter_k >= K:
            pass
        elif EVEN_K or block_end <= K:
            # No masking needed: either K is evenly divisible (EVEN_K)
            # or this block fits entirely within K
            tiled_b = tl.load(b_ptr)
            if USE_GDC:
                tl.extra.cuda.gdc_wait()
            tiled_a = tl.load(a_ptr)
            if CAST_TYPE:
                tiled_a = tiled_a.to(b_dtype)

            accumulator = _accumulate_mm(
                tiled_a,
                tiled_b,
                accumulator,
                a_scale_ptr,
                b_scale_ptr,
                a_scale_k_stride,
                b_scale_k_stride,
                iter_k,
                group_k,
                group_n,
                use_fp8_w8a8,
            )
        else:
            # Partial block at the tail: mask out-of-bounds elements
            k_offsets = tl.arange(0, BLOCK_K)
            mask = iter_k + k_offsets < K
            tiled_b = tl.load(b_ptr, mask=mask[:, None], other=0.0)
            if USE_GDC:
                tl.extra.cuda.gdc_wait()
            tiled_a = tl.load(a_ptr, mask=mask[None, :], other=0.0)
            if CAST_TYPE:
                tiled_a = tiled_a.to(b_dtype)

            accumulator = _accumulate_mm(
                tiled_a,
                tiled_b,
                accumulator,
                a_scale_ptr,
                b_scale_ptr,
                a_scale_k_stride,
                b_scale_k_stride,
                iter_k,
                group_k,
                group_n,
                use_fp8_w8a8,
            )

        a_ptr += STEP_K * ak_stride
        b_ptr += STEP_K * bk_stride

    return accumulator