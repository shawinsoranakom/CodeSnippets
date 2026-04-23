def do_expand_kernel_fp8(
    pid_n,
    lora_index,
    slice_id,
    input_ptr,
    lora_ptr,
    out_ptr,
    a_scale_ptr,
    b_scale_ptr,
    N,
    K,
    M_LEN,
    ram,  # array identifying the rows of Input ptr to operate on
    slice_start_loc,
    # input ptr strides
    input_d0_stride,
    input_d1_stride,
    input_d2_stride,
    # lora ptr strides
    ls_d0_ptr,
    ls_d1_ptr,
    ls_d2_ptr,
    # scale strides
    a_scale_m_stride,
    a_scale_k_stride,
    b_scale_l_stride,
    b_scale_n_stride,
    b_scale_k_stride,
    # out ptr strides
    output_d0_stride,
    output_d1_stride,
    # block size for block-wise quantization
    group_n: tl.constexpr,
    group_k: tl.constexpr,
    # constants
    BLOCK_M: tl.constexpr,
    BLOCK_N: tl.constexpr,
    BLOCK_K: tl.constexpr,
    SAME_STRIDE: tl.constexpr,
    SLICE_NUM: tl.constexpr,
    EVEN_K: tl.constexpr,
    CAST_TYPE: tl.constexpr,
    ADD_INPUTS: tl.constexpr,
    USE_GDC: tl.constexpr,
    use_fp8_w8a8: tl.constexpr,
    per_channel_quant: tl.constexpr,
):
    """
    FP8-compatible expand kernel for LoRA.
    Given an array of integers that identifies the rows of A, ram,
    a lora index that identifies which LoRA to use from lora_ptr, lora_index,
    a slice_id that identifies the input/output slice,
    compute the matrix product with FP8 quantization support and store in
    the appropriate output location.

    For expand kernel, the input (shrink output) may be in FP32/FP16/BF16,
    while the LoRA B weights can be in FP8.

    Supports:
    - FP8 W8A8 quantization for LoRA B weights
    - Block-wise quantization with configurable group_k and group_n
    - Per-channel quantization
    - Tensor-wise quantization
    """

    # ls_d*_ptr can be either an integer or a pointer
    if SAME_STRIDE:
        cur_lora_d0_stride = ls_d0_ptr
        cur_lora_d1_stride = ls_d1_ptr
        cur_lora_d2_stride = ls_d2_ptr
    else:
        cur_lora_d0_stride = tl.load(ls_d0_ptr + slice_id)
        cur_lora_d1_stride = tl.load(ls_d1_ptr + slice_id)
        cur_lora_d2_stride = tl.load(ls_d2_ptr + slice_id)

    # Identify the input_ptr and lora_ptr from slice_id.
    if SLICE_NUM == 1:
        cur_input_ptr = input_ptr
        if use_fp8_w8a8:
            cur_lora_ptr = lora_ptr
            cur_b_scale_ptr = b_scale_ptr
        else:
            cur_lora_ptr = lora_ptr
            cur_b_scale_ptr = b_scale_ptr  # May be None for non-quantized
    else:
        cur_input_ptr = input_ptr + slice_id * input_d0_stride
        if use_fp8_w8a8:
            cur_lora_ptr = tl.load(lora_ptr + slice_id).to(
                tl.pointer_type(tl.float8e4nv)
            )
            cur_b_scale_ptr = tl.load(b_scale_ptr + slice_id).to(
                tl.pointer_type(tl.float32)
            )
        else:
            cur_lora_ptr = tl.load(lora_ptr + slice_id).to(
                tl.pointer_type(out_ptr.dtype.element_ty)
            )
            cur_b_scale_ptr = (
                tl.load(b_scale_ptr + slice_id).to(tl.pointer_type(tl.float32))
                if b_scale_ptr is not None
                else None
            )

    # Identify the column indices of B to process.
    offset_n = tl.arange(0, BLOCK_N) + pid_n * BLOCK_N
    rbn = tl.max_contiguous(tl.multiple_of(offset_n % N, BLOCK_N), BLOCK_N)

    # Identify A and B block pointers
    offset_k = tl.arange(0, BLOCK_K)
    a_ptr = (
        cur_input_ptr
        + ram[:, None] * input_d1_stride
        + offset_k[None, :] * input_d2_stride
    )
    b_ptr = (
        cur_lora_ptr
        + cur_lora_d0_stride * lora_index
        + offset_k[:, None] * cur_lora_d2_stride
        + rbn[None, :] * cur_lora_d1_stride
    )

    # Setup scale pointers for FP8/INT8 quantization
    if use_fp8_w8a8:
        if group_k > 0 and group_n > 0:
            # Block-wise quantization - compute scale pointers for fp8_mm_k
            # a_scale: per-row base pointers, shape (BLOCK_M,)
            mm_a_scale_ptr = a_scale_ptr + ram * a_scale_m_stride

            # b_scale: pre-compute N-dimension offset since fp8_mm_k doesn't know pid_n
            n_offset = pid_n * BLOCK_N
            offs_ns = (n_offset + tl.arange(0, BLOCK_N)) // group_n
            # Base pointer with lora offset + N-group offset baked in, shape (BLOCK_N,)
            mm_b_scale_ptr = (
                cur_b_scale_ptr
                + lora_index * b_scale_l_stride
                + offs_ns * b_scale_n_stride
            )
        elif per_channel_quant:
            # Per-channel for weights, shape (BLOCK_N,)
            b_scale_ptrs = (
                cur_b_scale_ptr + lora_index * b_scale_l_stride + rbn * b_scale_n_stride
            )
            b_scale = tl.load(b_scale_ptrs)
            # Per-token activation scale, only if a_scale_ptr provided
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

    # Compute the block matrix product using fp8_mm_k
    # Note: For expand kernel, SPLIT_K=1, so we pass 1 for SPLIT_K
    accumulator = fp8_mm_k(
        a_ptr,
        b_ptr,
        mm_a_scale_ptr,
        mm_b_scale_ptr,
        input_d2_stride,  # ak_stride
        cur_lora_d2_stride,  # bk_stride
        a_scale_k_stride,
        b_scale_k_stride,
        offset_k,
        K,
        BLOCK_M,
        BLOCK_N,
        BLOCK_K,
        EVEN_K,
        1,  # SPLIT_K = 1 for expand kernel
        group_k,
        group_n,
        use_fp8_w8a8,
        per_channel_quant,
        CAST_TYPE,  # CAST_TYPE - cast FP8 B to A's dtype
        cur_lora_ptr.dtype.element_ty,
        USE_GDC,
        base_k=0,
    )

    # Apply dequantization scales for non-block-wise quantization
    if use_fp8_w8a8:
        if group_k > 0 and group_n > 0:
            pass  # Already applied per block in fp8_mm_k
        else:
            # Tensor-wise or per-channel: apply scales after accumulation
            accumulator = accumulator * a_scale * b_scale

    tiled_c = accumulator.to(out_ptr.dtype.element_ty)
    if SLICE_NUM == 1:
        cur_slice_start = slice_start_loc
    else:
        cur_slice_start = tl.load(slice_start_loc + slice_id)

    # Identify the C output pointers to store the results of the accumulator.
    offset_cn = tl.arange(0, BLOCK_N) + pid_n * BLOCK_N + cur_slice_start
    offset_cm = tl.arange(0, BLOCK_M)
    c_ptr = (
        out_ptr
        + ram[:, None] * output_d0_stride
        + offset_cn[None, :] * output_d1_stride
    )
    c_mask = (offset_cm[:, None] < M_LEN) & (offset_cn[None, :] < (cur_slice_start + N))

    if ADD_INPUTS:
        tiled_out = tl.load(c_ptr, mask=c_mask)
        tiled_c += tiled_out
    tl.store(c_ptr, tiled_c, mask=c_mask)