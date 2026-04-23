def test_contexted_kv_attention(
    num_heads: int,
    num_queries_per_kv: int,
    head_size: int,
    sliding_window: int,
    dtype: torch.dtype,
    kv_cache_dtype: str,
    device: str,
    op: Callable,
    block_size: int = 32,
) -> None:
    if "fp8" in kv_cache_dtype and not current_platform.has_device_capability(89):
        pytest.skip(
            "Triton limitation: fp8e4nv data type is not supported on CUDA arch < 89"
        )

    if (
        current_platform.is_rocm()
        and op is chunked_prefill_paged_decode
        and kv_cache_dtype == "fp8_e5m2"
    ):
        pytest.skip("ROCm custom paged attention does not support fp8_e5m2 KV cache")

    set_random_seed(0)
    torch.set_default_device(device)

    # Need this, otherwise when we capture the graph the process
    # for GPU 1 would run on both GPU0 and GPU1 and things would hang
    #
    # see also similar issue: https://github.com/Dao-AILab/flash-attention/issues/523
    torch.accelerator.set_device_index(device)

    MAX_SEQ_LEN = 1024
    MAX_CTX_LEN = 1024
    BS = 10
    cache_size = 640
    max_block_per_request = 64
    query_lens = [random.randint(16, MAX_SEQ_LEN) for _ in range(BS)]
    # ensure one sequence in batch is a decode
    query_lens[-1] = 1

    ctx_lens = [random.randint(16, MAX_CTX_LEN) for _ in range(BS)]
    seq_lens = [a + b for a, b in zip(query_lens, ctx_lens)]
    num_kv_heads = num_heads // num_queries_per_kv

    num_tokens = sum(query_lens)
    query = torch.empty(num_tokens, num_heads, head_size, dtype=dtype)
    query.uniform_(-1e-3, 1e-3)
    output = torch.empty(num_tokens, num_heads, head_size, dtype=dtype)

    kv = torch.empty(sum(seq_lens), 2, num_kv_heads, head_size, dtype=dtype)
    kv.uniform_(-1e-3, 1e-3)
    key, value = kv.unbind(dim=1)

    if kv_cache_dtype == "auto":
        cache_dtype = dtype
    else:
        cache_dtype = STR_DTYPE_TO_TORCH_DTYPE[kv_cache_dtype]
    k_cache = torch.zeros(
        cache_size, block_size, num_kv_heads, head_size, dtype=cache_dtype
    )
    v_cache = torch.zeros(
        cache_size, block_size, num_kv_heads, head_size, dtype=cache_dtype
    )
    k = torch.zeros(sum(query_lens), num_kv_heads, head_size, dtype=dtype)
    v = torch.zeros(sum(query_lens), num_kv_heads, head_size, dtype=dtype)
    values = torch.arange(0, cache_size, dtype=torch.int32)
    values = values[torch.randperm(cache_size)]
    block_table = values[: BS * max_block_per_request].view(BS, max_block_per_request)
    b_seq_len = torch.tensor(seq_lens, dtype=torch.int32)
    b_ctx_len = torch.tensor(ctx_lens, dtype=torch.int32)
    b_start_loc = torch.cumsum(torch.tensor([0] + query_lens), dim=0).to(torch.int32)
    max_input_len = MAX_SEQ_LEN
    # copy kv to cache
    b_seq_start_loc = torch.cumsum(torch.tensor([0] + seq_lens[:-1]), dim=0).to(
        torch.int32
    )
    for i in range(BS):
        for j in range(query_lens[i]):
            k[b_start_loc[i] + j].copy_(key[b_seq_start_loc[i] + b_ctx_len[i] + j])
            v[b_start_loc[i] + j].copy_(value[b_seq_start_loc[i] + b_ctx_len[i] + j])
        cur_ctx = 0
        block_id = 0
        while cur_ctx < b_ctx_len[i]:
            start_loc = b_seq_start_loc[i] + cur_ctx
            if cur_ctx + block_size > b_ctx_len[i]:
                end_loc = b_seq_start_loc[i] + b_ctx_len[i]
            else:
                end_loc = start_loc + block_size
            start_slot = block_table[i, block_id] * block_size
            end_slot = start_slot + end_loc - start_loc
            k_cache.view(-1, num_kv_heads, head_size)[start_slot:end_slot].copy_(
                key[start_loc:end_loc]
            )
            v_cache.view(-1, num_kv_heads, head_size)[start_slot:end_slot].copy_(
                value[start_loc:end_loc]
            )
            cur_ctx += block_size
            block_id += 1
    # transpose K_cache[num_blocks, block_size, num_kv_heads, head_size]
    # to K_cache[num_blocks, num_kv_heads, head_size/8, block_size, 8]
    k_cache = (
        k_cache.view(-1, block_size, num_kv_heads, head_size // 8, 8)
        .permute(0, 2, 3, 1, 4)
        .contiguous()
    )
    # transpose V_cache[num_blocks, block_size, num_kv_heads, head_size]
    # to V_cache[num_blocks, num_kv_heads, head_size, block_size]
    v_cache = (
        v_cache.view(-1, block_size, num_kv_heads, head_size)
        .permute(0, 2, 3, 1)
        .contiguous()
    )
    k_scale = v_scale = torch.tensor(1.0, dtype=torch.float32, device=device)

    # Warm up the Triton kernel by calling it once before actually measuring
    # generation time
    op(
        query,
        k,
        v,
        output,
        kv_cache_dtype,
        k_cache,
        v_cache,
        block_table,
        b_start_loc,
        b_seq_len,
        MAX_CTX_LEN,
        max_input_len,
        k_scale,
        v_scale,
        sliding_window=sliding_window,
    )
    torch.accelerator.synchronize()
    start_time = time.time()
    op(
        query,
        k,
        v,
        output,
        kv_cache_dtype,
        k_cache,
        v_cache,
        block_table,
        b_start_loc,
        b_seq_len,
        MAX_CTX_LEN,
        max_input_len,
        k_scale,
        v_scale,
        sliding_window=sliding_window,
    )
    torch.accelerator.synchronize()
    end_time = time.time()
    print(f"triton Time: {(end_time - start_time) * 1000:.2f} ms")

    scale = float(1.0 / (head_size**0.5))

    # Reshape for SDPA: (seq_len, num_heads, head_size) ->
    # (1, num_heads, seq_len, head_size)
    query_sdpa = query.view(num_tokens, num_kv_heads, num_queries_per_kv, head_size)
    query_sdpa = query_sdpa.permute(1, 2, 0, 3).reshape(
        1, num_heads, num_tokens, head_size
    )

    # Expand key and value for GQA/MQA to match query heads
    key_sdpa = key[:, :, None, :].expand(
        key.shape[0], num_kv_heads, num_queries_per_kv, key.shape[-1]
    )
    key_sdpa = key_sdpa.permute(1, 2, 0, 3).reshape(
        1, num_heads, sum(seq_lens), head_size
    )

    value_sdpa = value[:, :, None, :].expand(
        value.shape[0], num_kv_heads, num_queries_per_kv, value.shape[-1]
    )
    value_sdpa = value_sdpa.permute(1, 2, 0, 3).reshape(
        1, num_heads, sum(seq_lens), head_size
    )

    attn_mask = create_causal_attention_mask_for_sdpa(
        query_lens, seq_lens, sliding_window, device=device, dtype=dtype
    )

    output_ref = F.scaled_dot_product_attention(
        query_sdpa,
        key_sdpa,
        value_sdpa,
        attn_mask=attn_mask,
        dropout_p=0.0,
        scale=scale,
    )
    torch.accelerator.synchronize()
    start_time = time.time()
    output_ref = F.scaled_dot_product_attention(
        query_sdpa,
        key_sdpa,
        value_sdpa,
        attn_mask=attn_mask,
        dropout_p=0.0,
        scale=scale,
    )
    torch.accelerator.synchronize()
    end_time = time.time()
    print(f"PyTorch SDPA Time: {(end_time - start_time) * 1000:.2f} ms")

    # Reshape output back to (num_tokens, num_heads, head_size)
    output_ref = output_ref.view(num_heads, num_tokens, head_size)
    output_ref = output_ref.permute(1, 0, 2).contiguous()
    atol = 1e-3 if "fp8" in kv_cache_dtype else 1e-4
    torch.testing.assert_close(output, output_ref, atol=atol, rtol=0)