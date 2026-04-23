def test_flashinfer_prefill_with_paged_fp8_kv(
    seq_lens: list[tuple[int, int]],
    num_heads: tuple[int, int],
    head_size: int,
    dtype: torch.dtype,
    block_size: int,
    soft_cap: float | None,
) -> None:
    pytest.skip("TODO: fix the accuracy issue")
    torch.set_default_device("cuda")
    set_random_seed(0)
    num_seqs = len(seq_lens)
    query_lens = [x[0] for x in seq_lens]
    kv_lens = [x[1] for x in seq_lens]
    num_query_heads = num_heads[0]
    num_kv_heads = num_heads[1]
    assert num_query_heads % num_kv_heads == 0
    max_kv_len = max(kv_lens)
    scale = head_size**-0.5

    kv_cache_dtype = torch.float8_e4m3fn

    query = torch.randn(sum(query_lens), num_query_heads, head_size, dtype=dtype)
    NUM_BLOCKS_FP8 = 2048
    key_value_cache = torch.randn(
        NUM_BLOCKS_FP8, 2, block_size, num_kv_heads, head_size, dtype=dtype
    )
    key_cache, value_cache = torch.chunk(key_value_cache, 2, dim=1)
    key_cache /= head_size**0.5
    value_cache /= head_size**0.5

    k_scale = key_cache.amax().item() / 448.0
    v_scale = value_cache.amax().item() / 448.0

    kv_cache_fp8 = torch.cat([key_cache / k_scale, value_cache / v_scale], dim=1).to(
        kv_cache_dtype
    )

    assert kv_cache_fp8.shape == key_value_cache.shape
    max_num_blocks_per_seq = (max_kv_len + block_size - 1) // block_size
    block_tables = torch.randint(
        0, NUM_BLOCKS_FP8, (num_seqs, max_num_blocks_per_seq), dtype=torch.int32
    )

    qo_indptr = [0]
    kv_indptr = [0]
    kv_indices = []
    kv_last_page_lens = []
    for i in range(num_seqs):
        seq_len = kv_lens[i]
        assert seq_len > 0
        num_blocks = (seq_len + block_size - 1) // block_size
        kv_indices.extend(block_tables[i, :num_blocks])
        kv_indptr.append(kv_indptr[-1] + num_blocks)
        kv_last_page_len = seq_len % block_size
        if kv_last_page_len == 0:
            kv_last_page_len = block_size
        kv_last_page_lens.append(kv_last_page_len)
        qo_indptr.append(qo_indptr[-1] + query_lens[i])

    qo_indptr = torch.tensor(qo_indptr, dtype=torch.int32)
    kv_indptr = torch.tensor(kv_indptr, dtype=torch.int32)
    kv_indices = torch.tensor(kv_indices, dtype=torch.int32)
    kv_last_page_lens = torch.tensor(kv_last_page_lens, dtype=torch.int32)

    workspace_buffer = torch.empty(128 * 1024 * 1024, dtype=torch.int8)
    wrapper = flashinfer.BatchPrefillWithPagedKVCacheWrapper(workspace_buffer, "NHD")
    wrapper.plan(
        qo_indptr,
        kv_indptr,
        kv_indices,
        kv_last_page_lens,
        num_query_heads,
        num_kv_heads,
        head_size,
        block_size,
        q_data_type=dtype,
        kv_data_type=kv_cache_dtype,
        logits_soft_cap=soft_cap,
    )

    output = wrapper.run(query, kv_cache_fp8, k_scale=k_scale, v_scale=v_scale)

    ref_output = ref_paged_attn(
        query=query,
        key_cache=key_cache.squeeze(1),
        value_cache=value_cache.squeeze(1),
        query_lens=query_lens,
        kv_lens=kv_lens,
        block_tables=block_tables,
        scale=scale,
        soft_cap=soft_cap,
    )
    del query
    del block_tables
    # verify prefill fp8
    (
        torch.testing.assert_close(output, ref_output, atol=5e-2, rtol=1e-2),
        f"{torch.max(torch.abs(output - ref_output))}",
    )