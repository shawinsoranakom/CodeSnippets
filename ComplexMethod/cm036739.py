def tg_mxfp4_moe(
    router_logits,
    topk,
    num_experts,
    intermediate_size,
    hidden_size,
    hidden_states,
    hidden_states_scale,
    w13_weight,
    w13_weight_scale,
    w13_bias,
    w2_weight,
    w2_weight_scale,
    w2_bias,
    act_type,
    alpha,
    beta,
    limit,
    transpose_optimized: bool = False,
) -> torch.Tensor:
    sf_block_size = 32
    assert (
        w13_weight.dim() == 3
        and w13_weight.shape[0] == num_experts
        and w13_weight.shape[1] == intermediate_size * 2
        and w13_weight.shape[2] == hidden_size // 2
    )
    assert (
        w13_weight_scale.dim() == 3
        and w13_weight_scale.shape[0] == num_experts
        and w13_weight_scale.shape[1] == intermediate_size * 2
        and w13_weight_scale.shape[2] == hidden_size // sf_block_size
    )
    assert (
        w2_weight.dim() == 3
        and w2_weight.shape[0] == num_experts
        and w2_weight.shape[1] == hidden_size
        and w2_weight.shape[2] == intermediate_size // 2
    )
    assert (
        w2_weight_scale.dim() == 3
        and w2_weight_scale.shape[1] == hidden_size
        and w2_weight_scale.shape[2] == intermediate_size // sf_block_size
    )
    assert (
        w13_bias.dim() == 2
        and w13_bias.shape[0] == num_experts
        and w13_bias.shape[1] == intermediate_size * 2
    )
    assert (
        w2_bias.dim() == 2
        and w2_bias.shape[0] == num_experts
        and w2_bias.shape[1] == hidden_size
    )

    # Swap w1 and w3 as the definition of
    # swiglu is different in the trtllm-gen
    w13_weight_scale_ = w13_weight_scale.clone()
    w13_weight_ = w13_weight.clone()
    w13_bias_ = w13_bias.clone()
    w13_weight[:, :intermediate_size, :].copy_(w13_weight_[:, intermediate_size:, :])
    w13_weight[:, intermediate_size:, :].copy_(w13_weight_[:, :intermediate_size, :])
    w13_weight_scale[:, :intermediate_size, :].copy_(
        w13_weight_scale_[:, intermediate_size:, :]
    )
    w13_weight_scale[:, intermediate_size:, :].copy_(
        w13_weight_scale_[:, :intermediate_size, :]
    )
    w13_bias[:, :intermediate_size].copy_(w13_bias_[:, intermediate_size:])
    w13_bias[:, intermediate_size:].copy_(w13_bias_[:, :intermediate_size])

    # Interleave the weights and scaling factors for activation
    w13_weight_interleaved = []
    w13_weight_scale_interleaved = []
    w13_bias_interleaved = []
    for i in range(num_experts):
        w13_weight_interleaved.append(
            reorder_rows_for_gated_act_gemm(w13_weight[i].clone())
        )
        w13_weight_scale_interleaved.append(
            reorder_rows_for_gated_act_gemm(w13_weight_scale[i].clone())
        )
        w13_bias_interleaved.append(
            reorder_rows_for_gated_act_gemm(w13_bias[i].clone().reshape(-1, 1))
        )
    w13_weight = torch.stack(w13_weight_interleaved).reshape(
        num_experts, 2 * intermediate_size, hidden_size // 2
    )
    w13_weight_scale = torch.stack(w13_weight_scale_interleaved).reshape(
        num_experts, 2 * intermediate_size, hidden_size // 32
    )
    w13_bias = torch.stack(w13_bias_interleaved).reshape(
        num_experts, 2 * intermediate_size
    )

    # Shuffle weights and scaling factors for transposed mma output
    gemm1_weights_shuffled = []
    gemm1_scales_shuffled = []
    gemm2_weights_shuffled = []
    gemm2_scales_shuffled = []
    gemm1_bias_shuffled = []
    gemm2_bias_shuffled = []
    epilogue_tile_m = 128  # FIXME: this depends on the kernel internals
    _cache_permute_indices: dict[torch.Size, torch.Tensor] = {}
    if transpose_optimized:
        for i in range(num_experts):
            # w13 weight shuffling
            permute_indices = get_w2_permute_indices_with_cache(
                _cache_permute_indices,
                w13_weight[i].view(torch.uint8),
                epilogue_tile_m,
            )
            gemm1_weights_shuffled.append(
                w13_weight[i]
                .view(torch.uint8)[permute_indices.to(w13_weight.device)]
                .contiguous()
            )
            # w13 scale shuffling
            permute_sf_indices = get_w2_permute_indices_with_cache(
                _cache_permute_indices,
                w13_weight_scale[i].view(torch.uint8),
                epilogue_tile_m,
                num_elts_per_sf=16,
            )
            gemm1_scales_shuffled.append(
                nvfp4_block_scale_interleave(
                    w13_weight_scale[i]
                    .view(torch.uint8)[permute_sf_indices.to(w13_weight_scale.device)]
                    .contiguous()
                )
            )
            # w13 bias shuffling
            permute_bias_indices = get_w2_permute_indices_with_cache(
                _cache_permute_indices,
                w13_bias[i].clone().reshape(-1, 1),
                epilogue_tile_m,
            )
            gemm1_bias_shuffled.append(
                w13_bias[i]
                .clone()
                .reshape(-1, 1)[permute_bias_indices.to(w13_bias.device)]
                .contiguous()
            )
            # w2 weight shuffling
            permute_indices = get_w2_permute_indices_with_cache(
                _cache_permute_indices,
                w2_weight[i].view(torch.uint8),
                epilogue_tile_m,
            )
            gemm2_weights_shuffled.append(
                w2_weight[i]
                .view(torch.uint8)[permute_indices.to(w2_weight.device)]
                .contiguous()
            )
            # w2 scale shuffling
            permute_sf_indices = get_w2_permute_indices_with_cache(
                _cache_permute_indices,
                w2_weight_scale[i].view(torch.uint8),
                epilogue_tile_m,
                num_elts_per_sf=16,
            )
            gemm2_scales_shuffled.append(
                nvfp4_block_scale_interleave(
                    w2_weight_scale[i]
                    .view(torch.uint8)[permute_sf_indices.to(w2_weight_scale.device)]
                    .contiguous()
                )
            )
            # w2 bias shuffling
            permute_indices = get_w2_permute_indices_with_cache(
                _cache_permute_indices,
                w2_bias[i].clone().reshape(-1, 1),
                epilogue_tile_m,
            )
            gemm2_bias_shuffled.append(
                w2_bias[i]
                .clone()
                .reshape(-1, 1)[permute_indices.to(w2_bias.device)]
                .contiguous()
            )

    else:
        for i in range(num_experts):
            gemm1_weights_shuffled.append(
                shuffle_matrix_a(w13_weight[i].view(torch.uint8), epilogue_tile_m)
            )
            gemm1_scales_shuffled.append(
                shuffle_matrix_sf_a(
                    w13_weight_scale[i].view(torch.uint8), epilogue_tile_m
                )
            )

            gemm2_weights_shuffled.append(
                shuffle_matrix_a(w2_weight[i].view(torch.uint8), epilogue_tile_m)
            )
            gemm2_scales_shuffled.append(
                shuffle_matrix_sf_a(
                    w2_weight_scale[i].view(torch.uint8), epilogue_tile_m
                )
            )
            gemm1_bias_shuffled.append(
                shuffle_matrix_a(w13_bias[i].reshape(-1, 1), epilogue_tile_m)
            )
            gemm2_bias_shuffled.append(
                shuffle_matrix_a(w2_bias[i].reshape(-1, 1), epilogue_tile_m)
            )

    w13_weight = torch.stack(gemm1_weights_shuffled)
    w13_weight_scale = (
        torch.stack(gemm1_scales_shuffled)
        .reshape(num_experts, 2 * intermediate_size, hidden_size // sf_block_size)
        .view(torch.float8_e4m3fn)
    )
    w13_bias = torch.stack(gemm1_bias_shuffled).reshape(num_experts, -1)

    w2_weight = torch.stack(gemm2_weights_shuffled)
    w2_weight_scale = (
        torch.stack(gemm2_scales_shuffled)
        .reshape(num_experts, hidden_size, intermediate_size // sf_block_size)
        .view(torch.float8_e4m3fn)
    )
    w2_bias = torch.stack(gemm2_bias_shuffled).reshape(num_experts, -1)

    tg_result = trtllm_fp4_block_scale_moe(
        routing_logits=router_logits.to(torch.bfloat16),
        routing_bias=None,
        hidden_states=hidden_states,
        hidden_states_scale=hidden_states_scale,
        gemm1_weights=w13_weight,
        gemm1_weights_scale=w13_weight_scale,
        gemm1_bias=w13_bias,
        gemm1_alpha=alpha,
        gemm1_beta=beta,
        gemm1_clamp_limit=limit,
        gemm2_weights=w2_weight,
        gemm2_weights_scale=w2_weight_scale,
        gemm2_bias=w2_bias,
        output1_scale_scalar=None,
        output1_scale_gate_scalar=None,
        output2_scale_scalar=None,
        num_experts=num_experts,
        top_k=topk,
        n_group=None,
        topk_group=None,
        intermediate_size=intermediate_size,
        local_expert_offset=0,
        local_num_experts=num_experts,
        routed_scaling_factor=None,
        routing_method_type=1,  # renormalize
        do_finalize=True,
    )[0]
    return tg_result