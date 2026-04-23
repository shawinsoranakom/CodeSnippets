def test_attention_quant_pattern(
    num_qo_heads: int,
    num_kv_heads: int,
    head_size: int,
    batch_size: int,
    dtype: torch.dtype,
    custom_ops: str,
    model_name: str,
    model_class: type[AttentionQuantPatternModel],
    backend: AttentionBackendEnum,
    dist_init,
    monkeypatch,
    use_fresh_inductor_cache,
):
    """Test AttentionStaticQuantPattern fusion pass"""
    monkeypatch.setenv("VLLM_DISABLE_COMPILE_CACHE", "1")

    if backend == AttentionBackendEnum.FLASHINFER and (
        not current_platform.is_device_capability((10, 0)) or not has_flashinfer()
    ):
        # This also captures the FP4 case
        pytest.skip("FlashInfer attn fusion requires Blackwell and flashinfer")

    custom_ops_list = custom_ops.split(",") if custom_ops else []

    device = torch.device(f"{DEVICE_TYPE}:0")
    torch.set_default_dtype(dtype)
    torch.manual_seed(42)

    backend_cls = backend.get_class()
    block_size = backend_cls.get_preferred_block_size(16)

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
        cache_config=CacheConfig(cache_dtype="fp8"),
        attention_config=AttentionConfig(backend=backend),
    )

    # Create test inputs
    q = torch.randn(batch_size, num_qo_heads * head_size, dtype=dtype, device=device)
    k = torch.randn(batch_size, num_kv_heads * head_size, dtype=dtype, device=device)
    v = torch.randn(batch_size, num_kv_heads * head_size, dtype=dtype, device=device)

    # Mark first dimension as dynamic for realistic testing
    torch._dynamo.mark_dynamic(q, 0)
    torch._dynamo.mark_dynamic(k, 0)
    torch._dynamo.mark_dynamic(v, 0)

    # Run model directly without compilation and fusion
    vllm_config_unfused = copy.deepcopy(vllm_config)
    with (
        set_current_vllm_config(vllm_config_unfused),
        set_forward_context(attn_metadata=None, vllm_config=vllm_config_unfused),
    ):
        model_unfused = model_class(
            num_qo_heads=num_qo_heads,
            num_kv_heads=num_kv_heads,
            head_size=head_size,
            device=device,
            vllm_config=vllm_config_unfused,
            block_size=block_size,
        )
        model_unfused = model_unfused.to(device)
        result_unfused_0 = model_unfused(q, k, v)  # noqa: F841  HACK: See #131044

        forward_ctx = get_forward_context()
        forward_ctx.attn_metadata = model_unfused.build_attn_metadata(batch_size)

        # Run model directly without fusion
        # Still compile so query QuantFP8 has closer numerics
        compiled_unfused = torch.compile(model_unfused, fullgraph=True)
        result_unfused = compiled_unfused(q, k, v)

    # Run model with attn fusion enabled
    vllm_config.compilation_config.pass_config = PassConfig(
        fuse_attn_quant=True, eliminate_noops=True
    )
    with (
        set_current_vllm_config(vllm_config),
        set_forward_context(attn_metadata=None, vllm_config=vllm_config),
    ):
        model_fused = model_class(
            num_qo_heads=num_qo_heads,
            num_kv_heads=num_kv_heads,
            head_size=head_size,
            device=device,
            vllm_config=vllm_config,
            w=model_unfused.w,
            block_size=block_size,
        )
        model_fused = model_fused.to(device)

        forward_ctx = get_forward_context()
        forward_ctx.attn_metadata = model_fused.build_attn_metadata(batch_size)

        # Create test backend with fusion passes enabled
        noop_pass = NoOpEliminationPass(vllm_config)
        attn_pass = LazyInitPass(AttnQuantFusionPass, vllm_config)
        cleanup_pass = PostCleanupPass(vllm_config)

        test_backend = TestBackend(noop_pass, attn_pass, cleanup_pass)
        # HACK: See https://github.com/vllm-project/vllm/issues/31044
        result_fused_0 = model_fused(q, k, v)  # noqa: F841

        # Compile model with fusion enabled
        compiled_fused = torch.compile(
            model_fused, backend=test_backend, fullgraph=True
        )
        assert compiled_fused.attn._o_scale_float is None

        result_fused = compiled_fused(q, k, v)

        if backend == AttentionBackendEnum.FLASHINFER:
            # With the Flashinfer backend after the 1st round of the forward
            # pass, output quant scale should be loaded into the attn layer's
            # _o_scale_float, the 2nd round should reuse the loaded
            # _o_scale_float
            assert compiled_fused.attn._o_scale_float is not None
            result_fused_2 = compiled_fused(q, k, v)

            assert compiled_fused.attn._o_scale_float is not None

            torch.testing.assert_close(
                result_unfused, result_fused_2, atol=1e-2, rtol=1e-2
            )

    # Check attn fusion support
    quant_key: QuantKey = model_class.quant_key
    attn_fusion_supported = [
        layer.impl.fused_output_quant_supported(quant_key)
        for key, layer in vllm_config.compilation_config.static_forward_context.items()
    ]
    assert sum(attn_fusion_supported) == len(attn_fusion_supported), (
        "All layers should support attention fusion"
    )

    # Check quantization ops in the graph before and after fusion
    quant_op = (
        torch.ops.aten.reciprocal
        if "-quant_fp8" in custom_ops_list
        else QUANT_OPS[quant_key]
    )

    # Note: for fp8, fully_replaced=False because query quant ops remain in graph.
    # Only output quant ops are fused into attention.
    test_backend.check_before_ops([quant_op], fully_replaced=quant_key is kNvfp4Dynamic)

    # access the underlying `AttnQuantFusionPass` on the `LazyInitPass`
    assert attn_pass.pass_.matched_count == sum(attn_fusion_supported)

    # Check attention ops in the graph before and after fusion
    attn_nodes_pre = list(find_op_nodes(ATTN_OP, test_backend.graph_pre_pass))
    attn_nodes_post = list(find_op_nodes(ATTN_OP, test_backend.graph_post_pass))

    assert len(attn_nodes_pre) > 0, "Should have attention nodes before fusion"
    assert len(attn_nodes_pre) == len(attn_nodes_post), (
        "Should have same number of attention nodes before and after fusion"
    )
    assert attn_nodes_pre[0].kwargs.get("output_scale") is None, (
        "Attention should not have output_scale before fusion"
    )
    assert attn_nodes_post[0].kwargs.get("output_scale") is not None, (
        "Attention should have output_scale after fusion"
    )

    assert attn_nodes_pre[0].kwargs.get("output_block_scale") is None, (
        "Attention should not have output_block_scale before fusion"
    )

    kv_cache_dummy_dep_pre_is_none = (
        attn_nodes_pre[0].kwargs.get("kv_cache_dummy_dep") is None
    )
    kv_cache_dummy_dep_post_is_none = (
        attn_nodes_post[0].kwargs.get("kv_cache_dummy_dep") is None
    )
    assert not (kv_cache_dummy_dep_pre_is_none ^ kv_cache_dummy_dep_post_is_none), (
        "The kv_cache_dummy_dep should be consistent before and after fusion"
    )

    if quant_key.dtype == FP8_DTYPE:
        assert attn_nodes_post[0].kwargs.get("output_block_scale") is None, (
            "Attention should not have output_block_scale after FP8 fusion"
        )
    elif quant_key.dtype == FP4_DTYPE:
        assert attn_nodes_post[0].kwargs.get("output_block_scale") is not None, (
            "Attention should have output_block_scale after FP4 fusion"
        )

    # Check that results are close
    torch.testing.assert_close(result_unfused, result_fused, atol=1e-2, rtol=1e-2)