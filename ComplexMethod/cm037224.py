def context_attention_fwd(
    q,
    k,
    v,
    o,
    kv_cache_dtype: str,
    k_cache,
    v_cache,
    b_loc,
    b_start_loc,
    b_seq_len,
    max_seq_len,
    max_input_len,
    k_scale: torch.Tensor,
    v_scale: torch.Tensor,
    alibi_slopes=None,
    sliding_window=None,
    sm_scale=None,
    skip_decode=False,
    fp8_out_scale=None,
    sinks=None,
    is_block_table_ptr: bool = False,
    causal: bool = True,
):
    q_dtype_is_f32 = q.dtype is torch.float32

    # Turing does have tensor core for float32 multiplication
    # use ieee as fallback for triton kernels work. There is also
    # warning on vllm/config.py to inform users this fallback
    # implementation
    IN_PRECISION = "ieee" if IS_TURING and q_dtype_is_f32 else None

    # Conversion of FP8 Tensor from uint8 storage to
    # appropriate torch.dtype for interpretation by Triton
    if "fp8" in kv_cache_dtype:
        assert k_cache.dtype in [torch.uint8, current_platform.fp8_dtype()]
        assert v_cache.dtype in [torch.uint8, current_platform.fp8_dtype()]

        if kv_cache_dtype in ("fp8", "fp8_e4m3"):
            target_dtype = current_platform.fp8_dtype()
        elif kv_cache_dtype == "fp8_e5m2":
            target_dtype = torch.float8_e5m2
        else:
            raise ValueError("Unsupported FP8 dtype:", kv_cache_dtype)

        k_cache = k_cache.view(target_dtype)
        v_cache = v_cache.view(target_dtype)

    if (
        k_cache.dtype == torch.uint8
        or v_cache.dtype == torch.uint8
        and kv_cache_dtype == "auto"
    ):
        raise ValueError(
            "kv_cache_dtype='auto' unsupported for\
            FP8 KV Cache prefill kernel"
        )

    # shape constraints
    Lq, Lk, Lv = q.shape[-1], k.shape[-1], v.shape[-1]
    assert Lq == Lk and Lk == Lv
    # round up Lk to a power of 2 - this is required for Triton block size
    Lk_padded = triton.next_power_of_2(Lk)

    if sm_scale is None:
        sm_scale = 1.0 / (Lq**0.5)
    batch, head = b_seq_len.shape[0], q.shape[1]
    num_queries_per_kv = q.shape[1] // k.shape[1]

    assert batch + 1 == len(b_start_loc)

    # 0 means "disable"
    if sliding_window is None or sliding_window <= 0:
        sliding_window = 0

    if is_block_table_ptr:
        kv_element_size = k_cache.element_size()
        block_byte_stride = k_cache.stride(0) * kv_element_size
        # The physical starting point of the obtained KV Cache Pool
        base_addr = k_cache.data_ptr()

        mask = b_loc > 0
        processed_b_loc = torch.where(
            mask, (b_loc - base_addr) // block_byte_stride, b_loc
        ).to(torch.int32)
    else:
        processed_b_loc = b_loc.to(torch.int32)

    if alibi_slopes is not None:
        assert causal, "Non-causal prefix attention is not supported with alibi"
        assert sinks is None, "Sinks arg is not supported with alibi"
        assert fp8_out_scale is None, "FP8 output not supported with alibi"
        # need to reduce num. blocks when using fp32
        # due to increased use of GPU shared memory
        # if q.dtype is torch.float32:
        BLOCK = BASE_BLOCK // 2 if q_dtype_is_f32 else BASE_BLOCK
        # batch, head,
        grid = (batch, head, triton.cdiv(max_input_len, BLOCK))
        _fwd_kernel_alibi[grid](
            q,
            k,
            v,
            k_cache,
            v_cache,
            b_loc,
            sm_scale,
            k_scale,
            v_scale,
            b_start_loc,
            b_seq_len,
            alibi_slopes,
            v_cache.shape[3],
            k_cache.shape[4],
            o,
            b_loc.stride(0),
            b_loc.stride(1),
            q.stride(0),
            q.stride(1),
            q.stride(2),
            k.stride(0),
            k.stride(1),
            k.stride(2),
            v.stride(0),
            v.stride(1),
            v.stride(2),
            o.stride(0),
            o.stride(1),
            o.stride(2),
            k_cache.stride(0),
            k_cache.stride(1),
            k_cache.stride(2),
            k_cache.stride(3),
            k_cache.stride(4),  # [num_blocks, num_kv_heads, head_size/x, block_size, x]
            v_cache.stride(0),
            v_cache.stride(1),
            v_cache.stride(2),
            v_cache.stride(3),  # [num_blocks, num_kv_heads, head_size, block_size]
            num_queries_per_kv=num_queries_per_kv,
            IN_PRECISION=IN_PRECISION,
            BLOCK_M=BLOCK,
            BLOCK_DMODEL=Lk,
            BLOCK_DMODEL_PADDED=Lk_padded,
            BLOCK_N=BLOCK,
            SKIP_DECODE=skip_decode,
            num_warps=NUM_WARPS,
            num_stages=1,
        )
        return

    max_seq_len = 0 if max_seq_len is None else max_seq_len
    extra_kargs: dict[str, Any] = {}
    if current_platform.is_rocm():
        extra_kargs = {}

    real_block_size = v_cache.shape[3]
    is_pow2 = real_block_size > 0 and (real_block_size & (real_block_size - 1) == 0)
    # For standard models involving powers of 2,
    # follow the original logic (Llama 128/64)
    # For non-standard models (Qwen3-next block_size 544), set to 32.
    if is_pow2:
        BLOCK_M = 128
        BLOCK_N = 64
    else:
        BLOCK_M = 32
        BLOCK_N = 32

    # TRITON_BLOCK_SIZE is kept at 32 to ensure
    # correct alignment logic when the kernel handles
    # non-standard sizes (such as 544).
    TRITON_BLOCK_SIZE = 32

    grid_fn = lambda META: (batch, head, triton.cdiv(max_input_len, META["BLOCK_M"]))
    _fwd_kernel[grid_fn](
        q,
        k,
        v,
        k_cache,
        v_cache,
        sinks,
        processed_b_loc,
        sm_scale,
        k_scale,
        v_scale,
        1.0 / fp8_out_scale if fp8_out_scale is not None else 1.0,
        b_start_loc,
        b_seq_len,
        k_cache.shape[4],
        o,
        processed_b_loc.stride(0),
        processed_b_loc.stride(1),
        q.stride(0),
        q.stride(1),
        q.stride(2),
        k.stride(0),
        k.stride(1),
        k.stride(2),
        v.stride(0),
        v.stride(1),
        v.stride(2),
        o.stride(0),
        o.stride(1),
        o.stride(2),
        stride_k_cache_bs=k_cache.stride(0),
        stride_k_cache_h=k_cache.stride(1),
        stride_k_cache_d=k_cache.stride(2),
        stride_k_cache_bl=k_cache.stride(3),
        stride_k_cache_x=k_cache.stride(4),
        stride_v_cache_bs=v_cache.stride(0),
        stride_v_cache_h=v_cache.stride(1),
        stride_v_cache_d=v_cache.stride(2),
        stride_v_cache_bl=v_cache.stride(3),
        BLOCK_SIZE=TRITON_BLOCK_SIZE,
        PHYSICAL_BLOCK_SIZE=real_block_size,
        num_queries_per_kv=num_queries_per_kv,
        IN_PRECISION=IN_PRECISION,
        BLOCK_DMODEL=Lk,
        BLOCK_DMODEL_PADDED=Lk_padded,
        SLIDING_WINDOW=sliding_window,
        SKIP_DECODE=skip_decode,
        USE_FP8=fp8_out_scale is not None,
        BLOCK_M=BLOCK_M,
        BLOCK_N=BLOCK_N,
        num_unroll_cache=4,
        num_unroll_request=1,
        num_warps=4,
        num_stages=1,
        USE_SINKS=sinks is not None,
        CAUSAL=causal,
        **extra_kargs,
    )
    return