def reference_moe_impl(
    config: Config, weights: WeightTensors, rank_tensors: RankTensors
) -> torch.Tensor:
    if config.quant_dtype == "nvfp4":
        quant_blocksize = 16
        dtype = config.dtype

        w1_q = weights.w1
        w1_blockscale = weights.w1_scale
        w1_gs = weights.w1_gs

        w2_q = weights.w2
        w2_blockscale = weights.w2_scale
        w2_gs = weights.w2_gs

        a_global_scale = (
            (FLOAT8_E4M3_MAX * FLOAT4_E2M1_MAX)
            / torch.amax(rank_tensors.hidden_states.flatten(), dim=-1)
        ).to(torch.float32)

        assert w1_gs is not None
        assert w2_gs is not None
        assert w1_blockscale is not None
        assert w2_blockscale is not None

        assert w1_blockscale.shape[1] % 128 == 0
        assert w1_blockscale.shape[2] % 4 == 0
        assert w2_blockscale.shape[1] % 128 == 0
        assert w2_blockscale.shape[2] % 4 == 0

        a_fp4, a_scale_interleaved = ops.scaled_fp4_quant(
            rank_tensors.hidden_states, a_global_scale
        )

        a = dequantize_nvfp4_to_dtype(
            a_fp4,
            a_scale_interleaved,
            a_global_scale,
            dtype=dtype,
            device=a_fp4.device,
            block_size=quant_blocksize,
        )

        e = w1_q.shape[0]
        n = w1_q.shape[1] // 2
        k = w2_q.shape[1]

        w1 = torch.zeros((e, 2 * n, k), device="cuda", dtype=dtype)
        w2 = torch.zeros((e, k, n), device="cuda", dtype=dtype)

        for idx in range(0, e):
            w1[idx] = dequantize_nvfp4_to_dtype(
                w1_q[idx],
                w1_blockscale[idx],
                w1_gs[idx],
                dtype=dtype,
                device=w1_q.device,
                block_size=quant_blocksize,
            )
            w2[idx] = dequantize_nvfp4_to_dtype(
                w2_q[idx],
                w2_blockscale[idx],
                w2_gs[idx],
                dtype=dtype,
                device=w2_q.device,
                block_size=quant_blocksize,
            )
        a_scale = None
        w1_scale = None
        w2_scale = None
        quant_dtype = None
        per_act_token_quant = False
        block_shape = None
    else:
        a = rank_tensors.hidden_states
        a_scale = rank_tensors.hidden_states_scale
        w1 = weights.w1
        w1_scale = weights.w1_scale
        w2 = weights.w2
        w2_scale = weights.w2_scale
        quant_dtype = config.quant_dtype
        per_act_token_quant = config.is_per_act_token_quant
        block_shape = config.quant_block_shape

    return torch_experts(
        a=a,
        w1=w1,
        w2=w2,
        topk_weight=rank_tensors.topk_weights,
        topk_ids=rank_tensors.topk_ids,
        global_num_experts=config.E,
        expert_map=None,
        w1_scale=w1_scale,
        w2_scale=w2_scale,
        a1_scale=a_scale,
        quant_dtype=quant_dtype,
        per_act_token_quant=per_act_token_quant,
        block_shape=block_shape,
        apply_router_weights_on_input=config.topk == 1
        and config.supports_apply_weight_on_input(),
    )