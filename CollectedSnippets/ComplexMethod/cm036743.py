def test_triton_experts_no_mul_activation(
    m: int,
    n: int,
    k: int,
    topk: int,
    activation: MoEActivation,
):
    hidden_states, w1, w2, topk_weights, topk_ids = make_test_tensors(
        m, n, k, NUM_EXPERTS, topk
    )

    experts = TritonExperts(
        moe_config=make_dummy_moe_config(),
        quant_config=FUSED_MOE_UNQUANTIZED_CONFIG,
    )

    ws1_shape, ws2_shape, out_shape = experts.workspace_shapes(
        M=m,
        N=n,
        K=k,
        topk=topk,
        global_num_experts=NUM_EXPERTS,
        local_num_experts=NUM_EXPERTS,
        expert_tokens_meta=None,
        activation=activation,
    )

    # Verify workspace shapes are correct for no_mul activation
    # workspace1 should handle activation_out_dim = N (not N//2)
    assert ws1_shape == (m, topk, max(n, k)), (
        f"workspace1 shape mismatch: expected {(m, topk, max(n, k))}, got {ws1_shape}"
    )
    # workspace2 should handle max(N, K) for intermediate_cache1/cache3
    assert ws2_shape == (m, topk, max(n, k)), (
        f"workspace2 shape mismatch: expected {(m, topk, max(n, k))}, got {ws2_shape}"
    )
    assert out_shape == (m, k), (
        f"output shape mismatch: expected {(m, k)}, got {out_shape}"
    )

    workspace1 = torch.empty(
        ws1_shape[0] * ws1_shape[1] * ws1_shape[2],
        dtype=hidden_states.dtype,
        device=hidden_states.device,
    )
    workspace2 = torch.empty(
        ws2_shape[0] * ws2_shape[1] * ws2_shape[2],
        dtype=hidden_states.dtype,
        device=hidden_states.device,
    )
    output = torch.zeros(m, k, dtype=hidden_states.dtype, device=hidden_states.device)

    experts.apply(
        output=output,
        hidden_states=hidden_states,
        w1=w1,
        w2=w2,
        topk_weights=topk_weights,
        topk_ids=topk_ids,
        activation=activation,
        global_num_experts=NUM_EXPERTS,
        expert_map=None,
        a1q_scale=None,
        a2_scale=None,
        workspace13=workspace1,
        workspace2=workspace2,
        expert_tokens_meta=None,
        apply_router_weight_on_input=False,
    )

    assert output.shape == (m, k), f"Expected shape {(m, k)}, got {output.shape}"
    assert not torch.isnan(output).any(), "Output contains NaN"
    assert not torch.isinf(output).any(), "Output contains Inf"
    assert output.abs().sum() > 0, "Output is all zeros"