def _run_trtllm_integration(batch_spec):
    """Run TRTLLM attention through the full FlashInfer pipeline
    and compare against an SDPA reference."""
    set_random_seed(42)
    device = torch.device(f"{DEVICE_TYPE}:0")

    vllm_config = create_vllm_config(
        model_name=MODEL,
        max_model_len=max(batch_spec.seq_lens),
        block_size=BLOCK_SIZE,
        num_gpu_blocks=NUM_GPU_BLOCKS,
    )
    vllm_config.attention_config.use_trtllm_attention = True

    num_q_heads = vllm_config.model_config.get_num_attention_heads(
        vllm_config.parallel_config
    )
    num_kv_heads = vllm_config.model_config.get_num_kv_heads(
        vllm_config.parallel_config
    )
    head_size = vllm_config.model_config.get_head_size()
    dtype = vllm_config.model_config.dtype
    scale = 1.0 / (head_size**0.5)

    # 1. Generate data and compute SDPA reference
    all_q, all_k, all_v = [], [], []
    all_sdpa_out = []
    k_contexts, v_contexts = [], []

    for i in range(batch_spec.batch_size):
        s_len = batch_spec.seq_lens[i]
        q_len = batch_spec.query_lens[i]
        ctx_len = s_len - q_len

        q = torch.randn(q_len, num_q_heads, head_size, dtype=dtype, device=device)
        k_full = torch.randn(s_len, num_kv_heads, head_size, dtype=dtype, device=device)
        v_full = torch.randn(s_len, num_kv_heads, head_size, dtype=dtype, device=device)

        # SDPA reference (N=1, H, L, D)
        q_sdpa = q.unsqueeze(0).transpose(1, 2)
        k_sdpa = k_full.unsqueeze(0).transpose(1, 2)
        v_sdpa = v_full.unsqueeze(0).transpose(1, 2)

        if num_q_heads != num_kv_heads:
            repeats = num_q_heads // num_kv_heads
            k_sdpa = k_sdpa.repeat_interleave(repeats, dim=1)
            v_sdpa = v_sdpa.repeat_interleave(repeats, dim=1)

        def causal_mask_mod(b, h, q_idx, kv_idx, *, context_len):
            return (q_idx + context_len) >= kv_idx

        mask_fn = partial(causal_mask_mod, context_len=ctx_len)
        block_mask = create_block_mask(
            mask_fn, B=None, H=None, Q_LEN=q_len, KV_LEN=s_len, device=device
        )
        sdpa_out = flex_attention(
            q_sdpa,
            k_sdpa,
            v_sdpa,
            block_mask=block_mask,
            scale=scale,
            enable_gqa=True,
        )
        all_sdpa_out.append(sdpa_out.transpose(1, 2).squeeze(0))

        all_q.append(q)
        all_k.append(k_full[ctx_len:])
        all_v.append(v_full[ctx_len:])
        k_contexts.append(k_full[:ctx_len])
        v_contexts.append(v_full[:ctx_len])

    query_vllm = torch.cat(all_q, dim=0)
    key_vllm = torch.cat(all_k, dim=0)
    value_vllm = torch.cat(all_v, dim=0)
    sdpa_output = torch.cat(all_sdpa_out, dim=0)

    common_attn_metadata = create_common_attn_metadata(batch_spec, BLOCK_SIZE, device)

    # 2. Create HND KV cache
    kv_cache = _create_hnd_kv_cache(
        k_contexts,
        v_contexts,
        BLOCK_SIZE,
        num_kv_heads,
        head_size,
        dtype,
        device,
        NUM_GPU_BLOCKS,
        common_attn_metadata,
    )

    # 3. Run through FlashInfer with TRTLLM enabled
    set_kv_cache_layout("HND")
    get_kv_cache_layout.cache_clear()

    try:
        kv_cache_spec = FullAttentionSpec(
            block_size=BLOCK_SIZE,
            num_kv_heads=num_kv_heads,
            head_size=head_size,
            dtype=dtype,
        )
        layer_names = ["test_layer_0"]

        with (
            set_current_vllm_config(vllm_config),
            unittest.mock.patch(
                "vllm.utils.flashinfer.supports_trtllm_attention",
                return_value=True,
            ),
            unittest.mock.patch(
                "vllm.v1.attention.backends.flashinfer.get_per_layer_parameters",
                _mock_get_per_layer_parameters,
            ),
        ):
            builder = FlashInferMetadataBuilder(
                kv_cache_spec, layer_names, vllm_config, device
            )
            attn_metadata = builder.build(
                common_prefix_len=0,
                common_attn_metadata=common_attn_metadata,
            )

            # Verify the correct TRTLLM metadata types were produced.
            has_prefills = any(ql > 1 for ql in batch_spec.query_lens)
            has_decodes = any(ql == 1 for ql in batch_spec.query_lens)

            if has_prefills:
                assert isinstance(attn_metadata.prefill, TRTLLMPrefill), (
                    f"Expected TRTLLMPrefill, got {type(attn_metadata.prefill)}"
                )
            if has_decodes:
                assert isinstance(attn_metadata.decode, TRTLLMDecode), (
                    f"Expected TRTLLMDecode, got {type(attn_metadata.decode)}"
                )

            impl = FlashInferImpl(
                num_heads=num_q_heads,
                head_size=head_size,
                scale=scale,
                num_kv_heads=num_kv_heads,
                alibi_slopes=None,
                sliding_window=None,
                kv_cache_dtype="auto",
            )

            mock_layer = MockAttentionLayer(device)
            output = torch.empty_like(query_vllm)

            impl.do_kv_cache_update(
                mock_layer,
                key_vllm,
                value_vllm,
                kv_cache,
                attn_metadata.slot_mapping,
            )

            output = impl.forward(
                mock_layer,
                query_vllm,
                key_vllm,
                value_vllm,
                kv_cache,
                attn_metadata,
                output=output,
            )

        # 4. Compare against SDPA reference
        torch.testing.assert_close(
            output,
            sdpa_output,
            atol=1e-2,
            rtol=1e-2,
        )

    finally:
        set_kv_cache_layout(None)
        get_kv_cache_layout.cache_clear()