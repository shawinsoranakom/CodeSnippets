def test_trtllm_gen_mxfp8_block_scale_moe(
    topk: int,
    num_experts: int,
    num_tokens: int,
    intermediate_size: int,
    hidden_size: int,
    is_gated: bool,
):
    torch.manual_seed(42)
    device = "cuda:0"

    inter_size = intermediate_size * (2 if is_gated else 1)

    hidden_states = (
        torch.randn(num_tokens, hidden_size, device=device, dtype=torch.bfloat16) / 20
    )
    w13 = (
        torch.randn(
            num_experts,
            inter_size,
            hidden_size,
            device=device,
            dtype=torch.bfloat16,
        )
        / 20
    )
    w2 = (
        torch.randn(
            num_experts,
            hidden_size,
            intermediate_size,
            device=device,
            dtype=torch.bfloat16,
        )
        / 20
    )
    router_logits = torch.rand(
        num_tokens, num_experts, dtype=torch.float32, device=device
    )
    router_logits_kernel = router_logits.to(torch.bfloat16)

    # Quantize weights to MXFP8 and normalize scales to [E, M, K//32].
    w13_q, w13_scale = mxfp8_quantize(w13, is_sf_swizzled_layout=False)
    w2_q, w2_scale = mxfp8_quantize(w2, is_sf_swizzled_layout=False)
    if w13_scale.ndim == 1:
        w13_scale = w13_scale.view(
            num_experts,
            inter_size,
            hidden_size // 32,
        )
    if w2_scale.ndim == 1:
        w2_scale = w2_scale.view(num_experts, hidden_size, intermediate_size // 32)

    # Quantize activations to MXFP8.
    hidden_states_q, hidden_states_scale = mxfp8_quantize(
        hidden_states, is_sf_swizzled_layout=False
    )
    if hidden_states_scale.ndim == 1:
        hidden_states_scale = hidden_states_scale.view(num_tokens, hidden_size // 32)

    # Reference output using dequantized tensors + MXFP8 intermediate quantization.
    w13_ref = mxfp8_dequantize(w13_q, w13_scale).to(torch.float32)
    w2_ref = mxfp8_dequantize(w2_q, w2_scale).to(torch.float32)
    hidden_states_ref = mxfp8_dequantize(hidden_states_q, hidden_states_scale).to(
        torch.float32
    )
    bias13 = torch.zeros(
        num_experts,
        intermediate_size * (2 if is_gated else 1),
        device=device,
    )
    bias2 = torch.zeros(num_experts, hidden_size, device=device)
    ref = reference_moe(
        router_logits_kernel.to(torch.float32),
        topk,
        num_experts,
        hidden_states_ref,
        w13_ref,
        bias13,
        w2_ref,
        bias2,
        alpha=1.0,
        beta=0.0,
        limit=None,
        act_type="mxfp8",
        is_gated=is_gated,
    )

    # Shuffle weights/scales with the same indexed layout used by TRTLLM kernels.
    epilogue_tile_m = 128
    gemm1_weights_shuffled = []
    gemm1_scales_shuffled = []
    gemm2_weights_shuffled = []
    gemm2_scales_shuffled = []
    for i in range(num_experts):
        w13_rows = intermediate_size * (2 if is_gated else 1)
        w13_interleaved = w13_q[i].clone().reshape(w13_rows, -1)
        w13_scale_interleaved = w13_scale[i].clone().reshape(w13_rows, -1)
        if is_gated:
            w13_interleaved = reorder_rows_for_gated_act_gemm(w13_interleaved)
            w13_scale_interleaved = reorder_rows_for_gated_act_gemm(
                w13_scale_interleaved
            )
        gemm1_weights_shuffled.append(
            shuffle_matrix_a(w13_interleaved.view(torch.uint8), epilogue_tile_m)
            .contiguous()
            .view(w13_q.dtype)
        )
        gemm2_weights_shuffled.append(
            shuffle_matrix_a(w2_q[i].view(torch.uint8), epilogue_tile_m)
            .contiguous()
            .view(w2_q.dtype)
        )

        gemm1_scales_shuffled.append(
            shuffle_matrix_sf_a(
                w13_scale_interleaved.view(torch.uint8).reshape(w13_rows, -1),
                epilogue_tile_m,
            )
            .contiguous()
            .view(w13_scale.dtype)
        )
        gemm2_scales_shuffled.append(
            shuffle_matrix_sf_a(
                w2_scale[i].view(torch.uint8).reshape(hidden_size, -1), epilogue_tile_m
            )
            .contiguous()
            .view(w2_scale.dtype)
        )

    out = trtllm_fp8_block_scale_moe(
        routing_logits=router_logits_kernel,
        routing_bias=None,
        hidden_states=hidden_states_q,
        hidden_states_scale=hidden_states_scale,
        gemm1_weights=torch.stack(gemm1_weights_shuffled),
        gemm1_weights_scale=torch.stack(gemm1_scales_shuffled),
        gemm2_weights=torch.stack(gemm2_weights_shuffled),
        gemm2_weights_scale=torch.stack(gemm2_scales_shuffled),
        num_experts=num_experts,
        top_k=topk,
        n_group=None,
        topk_group=None,
        intermediate_size=intermediate_size,
        local_expert_offset=0,
        local_num_experts=num_experts,
        routed_scaling_factor=None,
        routing_method_type=1,  # renormalize routing
        use_shuffled_weight=True,
        weight_layout=0,  # MajorK
        fp8_quantization_type=Fp8QuantizationType.MxFp8,
    )

    # Block-scale MXFP8 kernels are approximate; require majority close.
    check_accuracy(ref, out, atol=0.1, rtol=0.85, percent=0.8)