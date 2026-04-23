def mm_k(
    a_ptr,
    b_ptr,
    ak_stride,
    bk_stride,
    offset_k,
    K: tl.constexpr,
    BLOCK_M: tl.constexpr,
    BLOCK_N: tl.constexpr,
    BLOCK_K: tl.constexpr,
    EVEN_K: tl.constexpr,
    SPLIT_K: tl.constexpr,
    CAST_TYPE: tl.constexpr,
    b_dtype: tl.constexpr,
    USE_GDC: tl.constexpr,
    base_k,
):
    """
    Given a_ptr and b_ptr, that identify the rows of A (m x k) and columns of
    B (k x n), iterate, through the K dimension to compute the partial/complete
    matrix block product.
    If SPLIT_K == 1, the output m x n product is complete.
    If SPLIT_K > 1, the thread block computes partial outputs. The partial
    outputs are then atomically summed in the caller code.
    Args:
        a_ptr: Array of pointers, identifying rows of A
        b_ptr: Array of pointers, identifying columns of B
        ak_stride: K dimension stride of the A matrix
        bk_stride: K dimension stride of the B matrix
        K: Length of the K dimension
        BLOCK_M: M dimension of the output block m x n
        BLOCK_N: N dimension of the output block m x n
        BLOCK_K: K dimension atom
        EVEN_K: True if the blocks of A and B can be loaded without any
          masking.
        SPLIT_K: Parameter signifying parallelism in the K dimension.
        CAST_TYPE: if True, cast the values from the A matrix to the B
          matrix dtype.
        b_dtype: datatype of the B matrix
        USE_GDC: Whether to use PDL. True indicates use.
        base_k: Base offset along K dimension for current SPLIT_K group
    """
    accumulator = tl.zeros((BLOCK_M, BLOCK_N), dtype=tl.float32)

    # Step size along K for each iteration
    STEP_K = BLOCK_K * SPLIT_K

    # Total number of iterations (compile-time constant)
    num_iters = tl.cdiv(K, STEP_K)

    for k in range(num_iters):
        # Current iteration's global K offset
        iter_k = k * STEP_K + base_k

        # Check if this iteration is completely valid (no masking needed)
        block_end = iter_k + BLOCK_K

        if EVEN_K:
            # K is divisible by BLOCK_K, no masking ever needed
            # pre-fetch lora weight
            tiled_b = tl.load(b_ptr)
            if USE_GDC:
                tl.extra.cuda.gdc_wait()
            tiled_a = tl.load(a_ptr)
            if CAST_TYPE:
                tiled_a = tiled_a.to(b_dtype)
            accumulator += tl.dot(tiled_a, tiled_b)
        else:
            # Check if we need element-wise masking
            if iter_k >= K:
                # Entire block out of range, skip
                pass
            elif block_end <= K:
                # Entire block in range, no masking needed (fast path)
                tiled_b = tl.load(b_ptr)
                if USE_GDC:
                    tl.extra.cuda.gdc_wait()
                tiled_a = tl.load(a_ptr)
                if CAST_TYPE:
                    tiled_a = tiled_a.to(b_dtype)
                accumulator += tl.dot(tiled_a, tiled_b)
            else:
                # Partial block, need masking (only last iteration)
                k_offsets = tl.arange(0, BLOCK_K)
                mask = iter_k + k_offsets < K
                tiled_b = tl.load(b_ptr, mask=mask[:, None], other=0.0)
                if USE_GDC:
                    tl.extra.cuda.gdc_wait()
                tiled_a = tl.load(a_ptr, mask=mask[None, :], other=0.0)
                if CAST_TYPE:
                    tiled_a = tiled_a.to(b_dtype)
                accumulator += tl.dot(tiled_a, tiled_b)

        a_ptr += STEP_K * ak_stride
        b_ptr += STEP_K * bk_stride

    return accumulator