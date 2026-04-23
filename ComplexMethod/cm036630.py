def make_fused_moe_layer(
    rank: int,
    layer_idx: int,
    test_config: TestConfig,
) -> FusedMoE:
    fml = FusedMoE(
        num_experts=test_config.num_experts,
        top_k=test_config.num_topk,
        hidden_size=test_config.hidden_size,
        intermediate_size=test_config.intermediate_size,
        prefix=f"dummy_layer_{layer_idx}",
        activation="silu",
        is_act_and_mul=True,
        params_dtype=test_config.weight_dtype,
    )

    device = torch.device(f"cuda:{rank}")

    from functools import partial

    _make_expert_weights = partial(
        make_expert_weights,
        layer_idx=layer_idx,
        global_num_experts=test_config.num_experts,
        tensor_device=device,
    )

    assert isinstance(fml.w13_weight.data, torch.Tensor)
    assert isinstance(fml.w2_weight.data, torch.Tensor)
    fml.w13_weight.data = fml.w13_weight.data.to(device=device)
    fml.w2_weight.data = fml.w2_weight.data.to(device=device)
    w13_weight = fml.w13_weight.data
    w2_weight = fml.w2_weight.data
    assert w13_weight.size(0) == test_config.num_local_experts
    for i in range(test_config.num_local_experts):
        g_i = rank * test_config.num_local_experts + i
        w13_weight_e = w13_weight[i]
        w2_weight_e = w2_weight[i]
        w13_weight_e.copy_(
            _make_expert_weights(
                global_expert_idx=g_i,
                tensor_shape=w13_weight_e.shape,
                tensor_dtype=w13_weight_e.dtype,
                is_column_major=False,
            )
        )
        w2_weight_e.copy_(
            _make_expert_weights(
                global_expert_idx=g_i,
                tensor_shape=w2_weight_e.shape,
                tensor_dtype=w2_weight_e.dtype,
                is_column_major=False,
            )
        )

    block_size = 16

    def block_quant_scales_shape(
        shape: tuple[int, ...], is_column_major: bool
    ) -> tuple[int, ...]:
        assert len(shape) == 3
        if not is_column_major:
            return (shape[0], shape[1] // block_size, shape[2] // block_size)
        else:
            return (shape[0], shape[2] // block_size, shape[1] // block_size)

    is_column_major = test_config.column_major_scales
    w13_weight_scale_inv = torch.empty(
        block_quant_scales_shape(w13_weight.shape, is_column_major),
        dtype=test_config.weight_dtype,
        device=device,
    )
    w2_weight_scale_inv = torch.empty(
        block_quant_scales_shape(w2_weight.shape, is_column_major),
        dtype=test_config.weight_dtype,
        device=device,
    )

    for i in range(test_config.num_local_experts):
        g_i = rank * test_config.num_local_experts + i
        w13_s_e = w13_weight_scale_inv[i]
        w2_s_e = w2_weight_scale_inv[i]
        w13_s_e.copy_(
            _make_expert_weights(
                global_expert_idx=g_i,
                tensor_shape=w13_s_e.shape,
                tensor_dtype=w13_s_e.dtype,
                # Fill data in row-major and then
                # transpose if test_config requires col-major.
                is_column_major=False,
            )
        )
        w2_s_e.copy_(
            _make_expert_weights(
                global_expert_idx=g_i,
                tensor_shape=w2_s_e.shape,
                tensor_dtype=w2_s_e.dtype,
                is_column_major=False,
            )
        )
    if is_column_major:
        w13_weight_scale_inv = torch.transpose(w13_weight_scale_inv, 1, 2)
        w2_weight_scale_inv = torch.transpose(w2_weight_scale_inv, 1, 2)
        assert not w13_weight_scale_inv.is_contiguous()
        assert not w2_weight_scale_inv.is_contiguous()

    # Add scales to the parameter list
    fml.w13_weight_scale_inv = torch.nn.Parameter(
        w13_weight_scale_inv, requires_grad=False
    )
    fml.w2_weight_scale_inv = torch.nn.Parameter(
        w2_weight_scale_inv, requires_grad=False
    )

    return fml