def do_shrink_kernel_fp8(
    pid_n,
    pid_sk,
    slice_id,
    lora_index,
    input_ptr,
    lora_ptr,
    out_ptr,
    a_scale_ptr,
    b_scale_ptr,
    N,
    K,
    M_LEN,
    ram,
    # input strides
    input_d0_stride,
    input_d1_stride,
    # lora strides
    lora_d0_stride,
    lora_d1_stride,
    lora_d2_stride,
    # scale strides
    a_scale_m_stride,
    a_scale_k_stride,
    b_scale_l_stride,
    b_scale_n_stride,
    b_scale_k_stride,
    # output strides
    output_d0_stride,
    output_d1_stride,
    output_d2_stride,
    scaling,
    # block size for block-wise quantization
    group_n: tl.constexpr,
    group_k: tl.constexpr,
    BLOCK_M: tl.constexpr,
    BLOCK_N: tl.constexpr,
    BLOCK_K: tl.constexpr,
    EVEN_K: tl.constexpr,
    SPLIT_K: tl.constexpr,
    SLICE_NUM: tl.constexpr,
    USE_GDC: tl.constexpr,
    use_fp8_w8a8: tl.constexpr,
    per_channel_quant: tl.constexpr,
    launch_pdl: tl.constexpr,
):
    """
    Given an array of integers that identifies the rows of A, ram,
    a lora index that identifies which LoRA to use from lora_ptr, lora_index,
    a slice_id that identifies the input/output slice, compute the
    matrix product and store in the appropriate output location.
    """

    # Identify the lora_ptr from slice_id.
    if SLICE_NUM == 1:
        cur_lora_ptr = lora_ptr
        cur_b_scale_ptr = b_scale_ptr
    else:
        cur_lora_ptr = (
            tl.load(lora_ptr + slice_id).to(tl.pointer_type(tl.float8e4nv))
            if b_scale_ptr is not None
            else tl.load(lora_ptr + slice_id).to(
                tl.pointer_type(input_ptr.dtype.element_ty)
            )
        )
        cur_b_scale_ptr = (
            tl.load(b_scale_ptr + slice_id).to(tl.pointer_type(tl.float32))
            if b_scale_ptr is not None
            else b_scale_ptr
        )

    # Identify the column indices of B to process.
    offset_n = tl.arange(0, BLOCK_N) + pid_n * BLOCK_N
    rbn = tl.max_contiguous(tl.multiple_of(offset_n % N, BLOCK_N), BLOCK_N)

    # Identify A and B block pointers
    offset_k = pid_sk * BLOCK_K + tl.arange(0, BLOCK_K)
    a_ptr = (
        input_ptr + ram[:, None] * input_d0_stride + offset_k[None, :] * input_d1_stride
    )
    b_ptr = (
        cur_lora_ptr
        + lora_d0_stride * lora_index
        + rbn[None, :] * lora_d1_stride
        + offset_k[:, None] * lora_d2_stride
    )

    # Load scales for tensor-wise or per-channel quantization (outside the loop)
    # Block-wise scales are loaded inside fp8_mm_k
    if use_fp8_w8a8:
        if group_k > 0 and group_n > 0:
            # Block-wise: compute scale pointers for fp8_mm_k
            # a_scale: per-row base pointers, shape (BLOCK_M,)
            # Each pointer points to the start of that row's scale data
            mm_a_scale_ptr = a_scale_ptr + ram * a_scale_m_stride

            # b_scale: pre-compute N-dimension offset
            # We need to bake in the N-group offset since fp8_mm_k doesn't know pid_n
            n_offset = pid_n * BLOCK_N
            offs_ns = (n_offset + tl.arange(0, BLOCK_N)) // group_n
            # Base pointer with lora offset + N-group offset baked in, shape (BLOCK_N,)
            mm_b_scale_ptr = (
                cur_b_scale_ptr
                + lora_index * b_scale_l_stride
                + offs_ns * b_scale_n_stride
            )
        elif per_channel_quant:
            # Per-channel for weights, per-token for activations
            b_scale_ptrs = (
                cur_b_scale_ptr + lora_index * b_scale_l_stride + rbn * b_scale_n_stride
            )
            b_scale = tl.load(b_scale_ptrs)
            # Per-token activation scale
            a_scale = tl.load(a_scale_ptr + ram * a_scale_m_stride)[:, None]
            # For non-block-wise, pass original pointers (not used in mm loop)
            mm_a_scale_ptr = a_scale_ptr
            mm_b_scale_ptr = cur_b_scale_ptr
        else:
            # Tensor-wise quantization
            a_scale = tl.load(a_scale_ptr) if a_scale_ptr is not None else 1.0
            b_scale = tl.load(cur_b_scale_ptr + lora_index * b_scale_l_stride)
            # For non-block-wise, pass original pointers (not used in mm loop)
            mm_a_scale_ptr = a_scale_ptr
            mm_b_scale_ptr = cur_b_scale_ptr
    else:
        # Non-quantized path
        mm_a_scale_ptr = a_scale_ptr
        mm_b_scale_ptr = cur_b_scale_ptr

    # Compute partial/complete block matrix product.
    accumulator = fp8_mm_k(
        a_ptr,
        b_ptr,
        mm_a_scale_ptr,
        mm_b_scale_ptr,
        input_d1_stride,
        lora_d2_stride,
        a_scale_k_stride,
        b_scale_k_stride,
        offset_k,
        K,
        BLOCK_M,
        BLOCK_N,
        BLOCK_K,
        EVEN_K,
        SPLIT_K,
        group_k,
        group_n,
        use_fp8_w8a8,
        per_channel_quant,
        False,
        cur_lora_ptr.dtype.element_ty,
        USE_GDC,
        base_k=pid_sk * BLOCK_K,
    )
    # GDC launch dependents hints the runtime system to launch dependent kernels.
    if USE_GDC:
        tl.extra.cuda.gdc_launch_dependents()

    # Apply dequantization scales for tensor-wise/per-channel quantization
    if use_fp8_w8a8:
        if group_k > 0 and group_n > 0:
            # Block-wise: already applied in fp8_mm_k
            pass
        else:
            # Tensor-wise or per-channel: apply scales after accumulation
            accumulator = accumulator * a_scale * b_scale

    # Apply LoRA scaling factor
    accumulator *= scaling

    # Identify the C output pointers to store the results of the accumulator.
    offset_cn = tl.arange(0, BLOCK_N) + pid_n * BLOCK_N
    offset_cm = tl.arange(0, BLOCK_M)
    cur_out_ptr = out_ptr if SLICE_NUM == 1 else out_ptr + slice_id * output_d0_stride
    c_ptr = (
        cur_out_ptr
        + ram[:, None] * output_d1_stride
        + offset_cn[None, :] * output_d2_stride
    )
    c_mask = (offset_cm[:, None] < M_LEN) & (offset_cn[None, :] < N)

    # Cast accumulator to output dtype
    accumulator = accumulator.to(out_ptr.dtype.element_ty)

    # handles write-back with reduction-splitting
    if SPLIT_K == 1:
        tl.store(c_ptr, accumulator, mask=c_mask)
    else:
        tl.atomic_add(c_ptr, accumulator, mask=c_mask, sem="relaxed")