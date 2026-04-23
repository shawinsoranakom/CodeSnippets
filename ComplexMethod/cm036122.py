def test_sparse_backend_decode_correctness(
    default_vllm_config,
    dist_init,
    backend_cls,
    batch_name,
    kv_cache_dtype,
    tensor_parallel_size,
    block_size,
    workspace_init,
    q_scale: float,
    k_scale: float,
):
    if kv_cache_dtype not in backend_cls.supported_kv_cache_dtypes:
        pytest.skip(f"{backend_cls.get_name()} does not support {kv_cache_dtype}")

    if (
        backend_cls == FlashMLASparseBackend
        and kv_cache_dtype.startswith("fp8")
        and kv_cache_dtype != "fp8_ds_mla"
    ):
        pytest.skip(
            "FlashMLA Sparse Attention backend fp8 only supports "
            "fp8_ds_mla kv-cache dtype"
        )

    supported_block_sizes = backend_cls.get_supported_kernel_block_sizes()
    if block_size not in supported_block_sizes:
        pytest.skip(
            f"{backend_cls.get_name()} does not support block_size={block_size}"
        )

    if backend_cls == FlashMLASparseBackend:
        ok, reason = flashmla.is_flashmla_sparse_supported()
        if not ok:
            pytest.skip(reason)
    elif backend_cls == FlashInferMLASparseBackend:
        if not current_platform.has_device_capability(100):
            pytest.skip("FlashInferMLASparseBackend requires SM 10.0 or higher")

    batch_spec = SPARSE_BACKEND_BATCH_SPECS[batch_name]
    use_fp8_ds_mla_quantization = kv_cache_dtype == "fp8_ds_mla"

    device = torch.device(DEVICE_TYPE)
    dtype = torch.bfloat16

    # Model hyper-parameters (kept intentionally small for the unit test)
    total_num_heads = 128
    # Compute per-rank heads for simulated TP
    num_heads = max(1, total_num_heads // tensor_parallel_size)

    kv_lora_rank = 512
    qk_nope_head_dim = 128
    qk_rope_head_dim = 64
    v_head_dim = 128
    head_size = kv_lora_rank + qk_rope_head_dim
    topk_tokens = 128

    max_seqlen = max(batch_spec.seq_lens)
    total_cache_tokens = sum(batch_spec.seq_lens)

    # Note: We use TP=1 to avoid multi-GPU requirements in CI.
    # The test simulates head partitioning via mocked methods below.
    vllm_config = create_vllm_config(
        model_name="deepseek-ai/DeepSeek-V2-Lite-Chat",
        tensor_parallel_size=1,
        max_model_len=max_seqlen,
        num_gpu_blocks=max(2048, cdiv(total_cache_tokens, block_size) + 1),
        block_size=block_size,
        hf_config_override={
            "index_topk": topk_tokens,
            "attn_module_list_cfg": [{"topk_tokens": topk_tokens}],
        },
    )
    model_config = vllm_config.model_config
    model_config.hf_text_config = SimpleNamespace(
        q_lora_rank=None,
        kv_lora_rank=kv_lora_rank,
        qk_nope_head_dim=qk_nope_head_dim,
        qk_rope_head_dim=qk_rope_head_dim,
        v_head_dim=v_head_dim,
        model_type="deepseek_v2",
    )
    model_config.dtype = dtype
    model_config.get_num_attention_heads = MethodType(
        lambda self, parallel_config: num_heads,
        model_config,
    )
    model_config.get_num_kv_heads = MethodType(
        lambda self, parallel_config: 1, model_config
    )
    model_config.get_head_size = MethodType(lambda self: head_size, model_config)
    model_config.get_sliding_window = MethodType(lambda self: None, model_config)

    kv_cache_spec = create_standard_kv_cache_spec(vllm_config)

    torch.manual_seed(0)

    scale = 1.0 / math.sqrt(head_size)

    # Shared MLA projection weights to keep reference and backend in sync
    W_UK = torch.rand(
        kv_lora_rank, num_heads, qk_nope_head_dim, dtype=dtype, device=device
    )
    W_UV = torch.rand(kv_lora_rank, num_heads, v_head_dim, dtype=dtype, device=device)

    # Build synthetic decode-only workload
    seq_lens = batch_spec.seq_lens
    query_lens = batch_spec.query_lens

    # Pre-compute positions and sparse indices for all tokens.
    # We need these BEFORE computing the reference to use sparse attention masks.
    total_query_tokens = sum(query_lens)
    positions = []
    for i in range(batch_spec.batch_size):
        s_len = seq_lens[i]
        q_len = query_lens[i]
        ctx_len = s_len - q_len
        for q_idx in range(q_len):
            positions.append(ctx_len + q_idx)

    # Create sparse indices with UNIQUE per-token offsets to catch bugs where
    # the kernel uses wrong indices for some tokens (e.g., due to incorrect
    # tensor shapes like [1, num_tokens, ...] instead of [num_tokens, 1, ...]).
    # Also include -1 masked indices to verify the kernel handles them correctly.
    sparse_indices = torch.empty(
        total_query_tokens, topk_tokens, dtype=torch.int32, device=device
    )
    for tok_idx in range(total_query_tokens):
        max_valid_idx = positions[tok_idx]
        offset = tok_idx * 7  # Prime number for varied offsets
        # Use only half the topk indices as valid, mask the rest with -1
        # This tests that the kernel correctly ignores -1 indices
        num_valid = min(topk_tokens // 2, max_valid_idx + 1)
        if num_valid > 0:
            valid_range = torch.arange(num_valid, device=device, dtype=torch.int32)
            tok_indices = (valid_range + offset) % (max_valid_idx + 1)
            # Pad with -1 for the remaining positions
            tok_indices = torch.cat(
                [
                    tok_indices,
                    torch.full(
                        (topk_tokens - num_valid,), -1, device=device, dtype=torch.int32
                    ),
                ]
            )
        else:
            tok_indices = torch.full(
                (topk_tokens,), -1, device=device, dtype=torch.int32
            )
            tok_indices[0] = 0  # At least one valid index
        sparse_indices[tok_idx] = tok_indices

    all_q_vllm, all_kv_c_vllm, all_k_pe_vllm = [], [], []
    kv_c_contexts, k_pe_contexts = [], []
    reference_outputs = []

    kv_cache_scale = torch.tensor(k_scale, dtype=torch.float32, device=device)
    global_token_idx = 0

    for i in range(batch_spec.batch_size):
        s_len = seq_lens[i]
        q_len = query_lens[i]
        ctx_len = s_len - q_len

        q_c = torch.rand(
            q_len,
            num_heads,
            qk_nope_head_dim + qk_rope_head_dim,
            dtype=dtype,
            device=device,
        )
        kv_c_full = torch.rand(s_len, kv_lora_rank, dtype=dtype, device=device)
        k_pe_full = torch.rand(s_len, 1, qk_rope_head_dim, dtype=dtype, device=device)

        if use_fp8_ds_mla_quantization:
            is_sm100 = torch.cuda.get_device_capability()[0] >= 10
            kv_c_full, k_pe_squeezed = _quantize_dequantize_fp8_ds_mla(
                kv_c_full,
                k_pe_full.squeeze(1),
                block_size=block_size,
                scale=kv_cache_scale,
                simulate_sm100_e8m0_scales=is_sm100,
            )
            k_pe_full = k_pe_squeezed.unsqueeze(1)

        q_nope, q_pe = q_c.split([qk_nope_head_dim, qk_rope_head_dim], dim=-1)
        ql_nope = torch.einsum("qnh,lnh->qnl", q_nope, W_UK)
        q_mqa = torch.cat([ql_nope, q_pe], dim=-1)

        k_mqa = torch.cat([kv_c_full, k_pe_full.squeeze(1)], dim=-1)
        v_mqa = kv_c_full

        # Compute sparse SDPA reference per query token using its sparse indices
        for q_idx in range(q_len):
            tok_sparse_idx = sparse_indices[global_token_idx]
            valid_mask = tok_sparse_idx >= 0
            valid_indices = tok_sparse_idx[valid_mask].long()

            q_tok = q_mqa[q_idx : q_idx + 1]  # [1, num_heads, head_dim]
            k_sparse = k_mqa[valid_indices]  # [num_valid, head_dim]
            v_sparse = v_mqa[valid_indices]  # [num_valid, kv_lora_rank]

            k_sparse = k_sparse.unsqueeze(1).expand(-1, num_heads, -1)
            v_sparse = v_sparse.unsqueeze(1).expand(-1, num_heads, -1)

            # SDPA: [1, num_heads, 1, head_dim] x [1, num_heads, num_valid, head_dim]
            q_sdpa_in = q_tok.unsqueeze(0).transpose(1, 2)
            k_sdpa_in = k_sparse.unsqueeze(0).transpose(1, 2)
            v_sdpa_in = v_sparse.unsqueeze(0).transpose(1, 2)

            sdpa_out = torch.nn.functional.scaled_dot_product_attention(
                q_sdpa_in, k_sdpa_in, v_sdpa_in, scale=scale
            )
            sdpa_out = sdpa_out.transpose(1, 2).squeeze(
                0
            )  # [1, num_heads, kv_lora_rank]

            sdpa_out = torch.einsum("qnl,lnv->qnv", sdpa_out, W_UV)
            reference_outputs.append(sdpa_out.flatten(start_dim=-2))

            global_token_idx += 1

        all_q_vllm.append(q_c)
        all_kv_c_vllm.append(kv_c_full[ctx_len:])
        all_k_pe_vllm.append(k_pe_full[ctx_len:])
        kv_c_contexts.append(kv_c_full[: ctx_len + 1])
        k_pe_contexts.append(k_pe_full[: ctx_len + 1])

    query_vllm = torch.cat(all_q_vllm, dim=0)
    kv_c_vllm = torch.cat(all_kv_c_vllm, dim=0)
    k_pe_vllm = torch.cat(all_k_pe_vllm, dim=0)
    sdpa_reference = torch.cat(reference_outputs, dim=0)

    vllm_config.cache_config.cache_dtype = kv_cache_dtype
    vllm_config.model_config.hf_config.index_topk = topk_tokens

    common_attn_metadata = create_common_attn_metadata(
        batch_spec,
        vllm_config.cache_config.block_size,
        device,
        arange_block_indices=True,
    )

    kv_cache = create_and_prepopulate_kv_cache(
        kv_c_contexts=kv_c_contexts,
        k_pe_contexts=k_pe_contexts,
        block_size=vllm_config.cache_config.block_size,
        head_size=head_size,
        dtype=dtype,
        device=device,
        num_blocks=vllm_config.cache_config.num_gpu_blocks,
        common_attn_metadata=common_attn_metadata,
        randomize_blocks=False,
        kv_cache_dtype=kv_cache_dtype,
        scale=kv_cache_scale,
    )

    builder_cls = backend_cls.get_builder_cls()
    builder = builder_cls(kv_cache_spec, ["placeholder"], vllm_config, device)
    metadata = builder.build(
        common_prefix_len=0, common_attn_metadata=common_attn_metadata
    )

    # Use the pre-computed sparse_indices for the mock indexer
    mock_indexer = SimpleNamespace(topk_indices_buffer=sparse_indices)

    kv_b_proj_weight = torch.cat([W_UK, W_UV], dim=-1)
    kv_b_proj_weight = kv_b_proj_weight.view(
        kv_lora_rank, num_heads * (qk_nope_head_dim + v_head_dim)
    )

    mock_kv_b_proj = ColumnParallelLinear(
        input_size=kv_lora_rank,
        output_size=num_heads * (qk_nope_head_dim + v_head_dim),
        bias=False,
    ).to(device=device, dtype=dtype)
    mock_kv_b_proj.weight = torch.nn.Parameter(kv_b_proj_weight.T.contiguous())

    impl_cls = backend_cls.get_impl_cls()
    with set_current_vllm_config(vllm_config):
        impl = impl_cls(
            num_heads=num_heads,
            head_size=head_size,
            scale=scale,
            num_kv_heads=1,
            alibi_slopes=None,
            sliding_window=None,
            kv_cache_dtype=vllm_config.cache_config.cache_dtype,
            logits_soft_cap=None,
            attn_type="decoder",
            kv_sharing_target_layer_name=None,
            q_lora_rank=None,
            kv_lora_rank=kv_lora_rank,
            qk_nope_head_dim=qk_nope_head_dim,
            qk_rope_head_dim=qk_rope_head_dim,
            qk_head_dim=qk_nope_head_dim + qk_rope_head_dim,
            v_head_dim=v_head_dim,
            kv_b_proj=mock_kv_b_proj,
            indexer=mock_indexer,
        )

        impl.process_weights_after_loading(dtype)

        # Create mock sparse MLA layer with weight matrices
        mock_layer = MockSparseMLAAttentionLayer(
            impl=impl,
            num_heads=num_heads,
            qk_nope_head_dim=qk_nope_head_dim,
            qk_rope_head_dim=qk_rope_head_dim,
            v_head_dim=v_head_dim,
            kv_lora_rank=kv_lora_rank,
            device=device,
            W_UK=W_UK,
            W_UV=W_UV,
            q_scale=q_scale,
            k_scale=k_scale,
        )

    out_buffer = torch.empty(
        metadata.num_actual_tokens, num_heads * v_head_dim, dtype=dtype, device=device
    )

    with torch.inference_mode():
        backend_output = mock_layer.forward_impl(
            query_vllm,
            kv_c_vllm,
            k_pe_vllm,
            kv_cache,
            metadata,
            out_buffer,
        )

    assert backend_output.shape == sdpa_reference.shape
    assert backend_output.dtype == sdpa_reference.dtype
    assert torch.isfinite(backend_output).all()

    # FP8 quantization introduces some error, but should be within reasonable bounds
    # BF16 (auto) should be very accurate, FP8 allows slightly more tolerance
    if kv_cache_dtype.startswith("fp8"):
        torch.testing.assert_close(
            backend_output, sdpa_reference, rtol=0.065, atol=0.05
        )
    else:
        torch.testing.assert_close(backend_output, sdpa_reference, rtol=0.01, atol=0.01)