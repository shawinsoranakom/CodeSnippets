def run_dispatch_test(
    test_case: RotaryEmbeddingTestCase,
    device: str,
):
    """Run a dispatch test for a RotaryEmbedding class."""
    vllm_config = VllmConfig(
        compilation_config=CompilationConfig(custom_ops=["all", "+apply_rotary_emb"])
    )
    get_cached_compilation_config.cache_clear()

    with set_current_vllm_config(vllm_config):
        rope = test_case.rope_class(**test_case.rope_kwargs).to(device=device)

        apply_rotary_emb = rope.apply_rotary_emb

        # Verify custom op is enabled
        if test_case.expect_forward_native:
            assert (
                apply_rotary_emb._forward_method != apply_rotary_emb.forward_native
            ), "Test setup error: ApplyRotaryEmb custom op should be enabled"

        # Setup call tracking
        call_tracker = {"forward_native_called": False, "forward_called": False}
        original_forward_native = apply_rotary_emb.forward_native
        original_forward = apply_rotary_emb.forward

        def tracked_forward_native(*args, **kwargs):
            call_tracker["forward_native_called"] = True
            return original_forward_native(*args, **kwargs)

        def tracked_forward(*args, **kwargs):
            call_tracker["forward_called"] = True
            return original_forward(*args, **kwargs)

        apply_rotary_emb.forward_native = tracked_forward_native
        apply_rotary_emb.forward = tracked_forward

        try:
            num_tokens = test_case.positions_shape[-1]
            num_q_heads = 8
            num_kv_heads = 2
            head_size = test_case.rope_kwargs["head_size"]
            max_position = test_case.rope_kwargs["max_position_embeddings"]

            positions = torch.randint(
                0, max_position // 4, test_case.positions_shape, device=device
            )
            query = torch.randn(
                num_tokens, num_q_heads * head_size, dtype=torch.bfloat16, device=device
            )
            key = torch.randn(
                num_tokens,
                num_kv_heads * head_size,
                dtype=torch.bfloat16,
                device=device,
            )

            # Call the method under test
            method = getattr(rope, test_case.method_name)
            method(positions, query.clone(), key.clone())

            # Verify expectations
            if test_case.expect_forward_native:
                assert call_tracker["forward_native_called"], (
                    f"{test_case.name} should call ApplyRotaryEmb.forward_native()"
                )
            if not test_case.expect_forward:
                assert not call_tracker["forward_called"], (
                    f"{test_case.name} should NOT call ApplyRotaryEmb.forward(). "
                    "Bug: when +apply_rotary_emb is enabled, forward_native() "
                    "incorrectly dispatches to CUDA/HIP kernels."
                )
            if test_case.expect_forward:
                assert call_tracker["forward_called"], (
                    f"{test_case.name} should call ApplyRotaryEmb.forward()"
                )
        finally:
            apply_rotary_emb.forward_native = original_forward_native
            apply_rotary_emb.forward = original_forward