def test_mla_attention_quant_pattern(
    num_heads: int,
    qk_nope_head_dim: int,
    qk_rope_head_dim: int,
    v_head_dim: int,
    kv_lora_rank: int,
    batch_size: int,
    dtype: torch.dtype,
    custom_ops: str,
    model_name: str,
    model_class: type[MLAAttentionQuantPatternModel],
    backend: AttentionBackendEnum,
    dist_init,
    monkeypatch,
    use_fresh_inductor_cache,
):
    """Test MLA AttentionQuantPattern fusion pass"""
    if (
        model_class is TestMLAAttentionNvfp4QuantPatternModel
        and not is_nvfp4_supported()
    ):
        pytest.skip("NVFP4 is not supported on this GPU (requires SM 100+).")

    monkeypatch.setenv("VLLM_DISABLE_COMPILE_CACHE", "1")

    custom_ops_list = custom_ops.split(",") if custom_ops else []

    device = torch.device(f"{DEVICE_TYPE}:0")
    torch.set_default_dtype(dtype)
    torch.manual_seed(42)

    model_config = ModelConfig(
        model=model_name,
        max_model_len=2048,
        dtype=dtype,
    )
    vllm_config = VllmConfig(
        model_config=model_config,
        scheduler_config=SchedulerConfig(
            max_num_seqs=1024,
            max_model_len=model_config.max_model_len,
            is_encoder_decoder=model_config.is_encoder_decoder,
        ),
        compilation_config=CompilationConfig(
            mode=CompilationMode.VLLM_COMPILE,
            custom_ops=custom_ops_list,
        ),
        cache_config=CacheConfig(cache_dtype="auto"),
        attention_config=AttentionConfig(backend=backend),
    )

    # MLA inputs: q(B, N, qk_head_dim), kv_c_normed(B, L), k_pe(B, 1, R)
    qk_head_dim = qk_nope_head_dim + qk_rope_head_dim
    q = torch.randn(batch_size, num_heads, qk_head_dim, dtype=dtype, device=device)
    kv_c_normed = torch.randn(batch_size, kv_lora_rank, dtype=dtype, device=device)
    k_pe = torch.randn(batch_size, 1, qk_rope_head_dim, dtype=dtype, device=device)

    # Mark first dimension as dynamic
    torch._dynamo.mark_dynamic(q, 0)
    torch._dynamo.mark_dynamic(kv_c_normed, 0)
    torch._dynamo.mark_dynamic(k_pe, 0)

    # Run model without fusion
    vllm_config_unfused = copy.deepcopy(vllm_config)
    with (
        set_current_vllm_config(vllm_config_unfused),
        set_forward_context(attn_metadata=None, vllm_config=vllm_config_unfused),
    ):
        model_unfused = model_class(
            num_heads=num_heads,
            qk_nope_head_dim=qk_nope_head_dim,
            qk_rope_head_dim=qk_rope_head_dim,
            v_head_dim=v_head_dim,
            kv_lora_rank=kv_lora_rank,
            kv_cache_dtype=dtype,
            device=device,
            vllm_config=vllm_config_unfused,
        )
        model_unfused = model_unfused.to(device)
        # HACK: See #131044
        result_unfused_0 = model_unfused(q, kv_c_normed, k_pe)  # noqa: F841

        forward_ctx = get_forward_context()
        forward_ctx.attn_metadata = model_unfused.build_attn_metadata(batch_size)

        compiled_unfused = torch.compile(model_unfused, fullgraph=True)
        result_unfused = compiled_unfused(q, kv_c_normed, k_pe)

    # Run model with attn fusion enabled
    vllm_config.compilation_config.pass_config = PassConfig(
        fuse_attn_quant=True, eliminate_noops=True
    )
    with (
        set_current_vllm_config(vllm_config),
        set_forward_context(attn_metadata=None, vllm_config=vllm_config),
    ):
        model_fused = model_class(
            num_heads=num_heads,
            qk_nope_head_dim=qk_nope_head_dim,
            qk_rope_head_dim=qk_rope_head_dim,
            v_head_dim=v_head_dim,
            kv_lora_rank=kv_lora_rank,
            kv_cache_dtype=dtype,
            device=device,
            vllm_config=vllm_config,
            w=model_unfused.w,
            kv_b_proj_weight=model_unfused.kv_b_proj_weight,
        )
        model_fused = model_fused.to(device)

        forward_ctx = get_forward_context()
        forward_ctx.attn_metadata = model_fused.build_attn_metadata(batch_size)

        # Create test backend with fusion passes
        noop_pass = NoOpEliminationPass(vllm_config)
        attn_pass = LazyInitPass(MLAAttnQuantFusionPass, vllm_config)
        cleanup_pass = PostCleanupPass(vllm_config)

        test_backend = TestBackend(noop_pass, attn_pass, cleanup_pass)
        # HACK: See https://github.com/vllm-project/vllm/issues/31044
        result_fused_0 = model_fused(q, kv_c_normed, k_pe)  # noqa: F841

        compiled_fused = torch.compile(
            model_fused, backend=test_backend, fullgraph=True
        )

        result_fused = compiled_fused(q, kv_c_normed, k_pe)

    # Check attn fusion support
    quant_key: QuantKey = model_class.quant_key
    attn_fusion_supported = [
        layer.impl.fused_output_quant_supported(quant_key)
        for key, layer in vllm_config.compilation_config.static_forward_context.items()
        if isinstance(layer, MLAAttention)
    ]
    assert sum(attn_fusion_supported) == len(attn_fusion_supported), (
        "All MLA layers should support attention fusion"
    )

    # Check quantization ops in the graph
    is_per_group = quant_key.scale.group_shape.is_per_group()
    quant_op = (
        torch.ops.aten.reciprocal
        if "-quant_fp8" in custom_ops_list
        else QUANT_OPS[quant_key]
    )
    test_backend.check_before_ops([quant_op], fully_replaced=is_per_group)

    assert attn_pass.pass_.matched_count == sum(attn_fusion_supported)

    # Check MLA attention ops in the graph
    attn_nodes_pre = list(find_op_nodes(MLA_ATTN_OP, test_backend.graph_pre_pass))
    attn_nodes_post = list(find_op_nodes(MLA_ATTN_OP, test_backend.graph_post_pass))

    assert len(attn_nodes_pre) > 0, "Should have MLA attention nodes before fusion"
    assert len(attn_nodes_pre) == len(attn_nodes_post), (
        "Should have same number of MLA attention nodes before and after fusion"
    )

    # Before fusion: neither scale should be set
    assert attn_nodes_pre[0].kwargs.get("output_scale") is None
    assert attn_nodes_pre[0].kwargs.get("output_block_scale") is None

    # After fusion: derive expected scale presence from quant_key properties.
    # - output_scale: present for static quant or non-FP8 (NVFP4 carries input_scale)
    # - output_block_scale: present when quant uses per-group/block scaling
    has_output_scale = attn_nodes_post[0].kwargs.get("output_scale") is not None
    has_block_scale = attn_nodes_post[0].kwargs.get("output_block_scale") is not None

    expects_output_scale = quant_key.scale.static or quant_key.dtype != FP8_DTYPE
    assert has_output_scale == expects_output_scale, (
        f"output_scale: expected present={expects_output_scale}, got {has_output_scale}"
    )
    assert has_block_scale == is_per_group, (
        f"output_block_scale: expected present={is_per_group}, got {has_block_scale}"
    )

    # Check numerical correctness
    torch.testing.assert_close(result_unfused, result_fused, atol=1e-2, rtol=1e-2)