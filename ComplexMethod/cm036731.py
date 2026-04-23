def _run_one_config(
    vllm_config: VllmConfig,
    ep_size: int,
    dp_size: int,
    tp_size: int,
    dp_rank: int,
    tp_rank: int,
    m: int,
    n: int,
    k: int,
    num_experts: int,
    top_k: int,
    quantization: str | None,
    backend: str | None,
    test_body_fn: Callable,
    use_shared_experts: bool,
    use_gate: bool,
    use_routed_input_transform: bool,
    **kwargs,
) -> None:
    set_random_seed(7)

    """Generic test loop that sets up environment and delegates to test_body_fn.

    This function is called directly by test_moe_layer and test_moe_layer_eplb
    via parallel_launch_with_config, passing either _test_body_regular or
    _test_body_eplb as the test_body_fn parameter.
    """
    world_size = tp_size * dp_size
    use_ep = ep_size > 1

    assert vllm_config.parallel_config.enable_expert_parallel == use_ep

    in_dtype = torch.bfloat16
    device = torch.accelerator.current_accelerator()

    if not is_workspace_manager_initialized():
        init_workspace_manager(device)

    # Create test data and transforms
    test_data = setup_moe_test_data(
        m=m,
        k=k,
        n=n,
        num_experts=num_experts,
        in_dtype=in_dtype,
        use_shared_experts=use_shared_experts,
        use_gate=use_gate,
        use_routed_input_transform=use_routed_input_transform,
        backend=backend,
        device=device,
    )

    # Extract data from test_data
    hidden_states = test_data.hidden_states
    router_logits = test_data.router_logits
    w1 = test_data.w1
    w2 = test_data.w2
    shared_experts_config = test_data.shared_experts_config
    gate = test_data.gate
    routed_input_transform = test_data.routed_input_transform
    routed_output_transform = test_data.routed_output_transform
    activation = "silu"

    baseline_layer = make_fake_moe_layer(
        w1=w1,
        w2=w2,
        top_k=top_k,
        global_num_experts=num_experts,
        in_dtype=in_dtype,
        quantization=quantization,
        renormalize=False,
        shared_experts_config=shared_experts_config,
        gate=gate,
        routed_input_transform=routed_input_transform,
        routed_output_transform=routed_output_transform,
        use_ep=use_ep,
        tp_size=tp_size,
        ep_size=ep_size,
        dp_size=dp_size,
        activation=activation,
    )

    baseline_output = baseline_layer(hidden_states, router_logits)

    del baseline_layer
    torch.accelerator.empty_cache()

    with set_current_vllm_config(vllm_config):
        # Chunk weights for EP/TP (after baseline is created)
        if ep_size > 1:
            w1 = chunk_by_rank(w1, dp_rank, dp_size, dim=0, device=device)
            w2 = chunk_by_rank(w2, dp_rank, dp_size, dim=0, device=device)

        if tp_size > 1:
            w1 = tp_chunk_gate_up(w1, tp_rank, tp_size, dim=1, device=device)
            w2 = chunk_by_rank(w2, tp_rank, tp_size, dim=2, device=device)

        # Setup shared experts if needed
        shared_experts = create_shared_experts_from_config(
            shared_experts_config, in_dtype, tp_size, tp_rank, device
        )

        # Determine hidden size for MoE layer
        # When using routed_input_transform, experts operate in latent space
        hidden_size_for_layer = k // 2 if routed_input_transform is not None else k

        # Create initial MoE layer
        moe_layer = make_fused_moe_layer(
            quantization=quantization,
            use_ep=use_ep,
            hidden_size=hidden_size_for_layer,
            intermediate_size=n,
            in_dtype=in_dtype,
            tp_size=tp_size,
            ep_size=ep_size,
            dp_size=dp_size,
            w1=w1,
            w2=w2,
            top_k=top_k,
            global_num_experts=num_experts,
            shared_experts=shared_experts,
            gate=gate,
            routed_input_transform=routed_input_transform,
            routed_output_transform=routed_output_transform,
            activation=activation,
        )

        if moe_layer._expert_map is not None:
            moe_layer._expert_map = moe_layer._expert_map.to(device)

        num_tokens = m
        num_tokens_across_dp = torch.tensor(
            [num_tokens] * world_size,
            device=device,
            dtype=torch.int,
        )

        # Call the test body function with all necessary context
        expected, actual = test_body_fn(
            moe_layer=moe_layer,
            hidden_states=hidden_states,
            router_logits=router_logits,
            vllm_config=vllm_config,
            num_tokens=num_tokens,
            num_tokens_across_dp=num_tokens_across_dp,
            in_dtype=in_dtype,
            quantization=quantization,
            use_ep=use_ep,
            tp_size=tp_size,
            ep_size=ep_size,
            dp_size=dp_size,
            w1=w1,
            w2=w2,
            num_experts=num_experts,
            k=k,
            n=n,
            m=m,
            top_k=top_k,
            shared_experts=shared_experts,
            gate=gate,
            routed_input_transform=routed_input_transform,
            routed_output_transform=routed_output_transform,
            baseline_output=baseline_output,
            **kwargs,
        )

    # Common tolerance logic
    # TODO: consider associating tolerances with quant methods.
    if quantization is None:
        if k >= 2048:
            atol, rtol = 7.6e-2, 7.6e-2
        else:
            atol, rtol = 3.5e-2, 3.5e-2
    elif quantization in ("fp8", "fp8_blocked", "modelopt_fp8"):
        atol, rtol = 6e-2, 6e-2
    elif quantization == "modelopt_fp4":
        if k >= 2048:
            atol = rtol = 1e-1 + (k * 1e-4)
        else:
            atol = rtol = 1e-1

        if backend == "allgather_reducescatter" and tp_size > 1:
            atol += 2e-1
            rtol += 2e-1
    else:
        atol, rtol = 6e-2, 6e-2

    torch.accelerator.synchronize()  # TODO: Is this needed?
    torch.testing.assert_close(expected, actual, atol=atol, rtol=rtol)