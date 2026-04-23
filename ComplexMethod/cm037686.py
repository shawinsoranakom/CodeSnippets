def flashinfer_trtllm_mxint4_moe(
    x: torch.Tensor,
    router_logits: torch.Tensor,
    w13_weight_packed: torch.Tensor,
    w13_weight_scale: torch.Tensor,
    w2_weight_packed: torch.Tensor,
    w2_weight_scale: torch.Tensor,
    global_num_experts: int,
    top_k: int,
    intermediate_size_per_partition: int,
    local_num_experts: int,
    ep_rank: int = 0,
    num_expert_group: int | None = None,
    topk_group: int | None = None,
    e_score_correction_bias: torch.Tensor | None = None,
    routing_method_type: int | None = None,
) -> torch.Tensor:
    """
    Apply FlashInfer TensorRT-LLM MxInt4 MoE kernel.

    Args:
        x: Input hidden states. dtype: bfloat16
        router_logits: Router logits for expert selection. dtype: bfloat16/float32
        w13_weight_packed: Packed gate+up weights. dtype: uint8
        w13_weight_scale: Scales for gate+up weights. dtype: bfloat16
        w2_weight_packed: Packed down weights. dtype: uint8
        w2_weight_scale: Scales for down weights. dtype: bfloat16
        global_num_experts: Total number of experts across all ranks
        top_k: Number of experts to select per token
        intermediate_size_per_partition: Intermediate size per partition
        local_num_experts: Number of experts on this rank
        ep_rank: Expert parallelism rank (default: 0)
        num_expert_group: Number of expert groups (default: None -> 0)
        topk_group: Top-k within groups (default: None -> 0)
        e_score_correction_bias: Optional routing bias. dtype: bfloat16
        routing_method_type: FlashInfer RoutingMethodType enum value

    Returns:
        Output tensor from MoE layer. dtype: same as x (bfloat16)
    """
    from flashinfer import RoutingMethodType
    from flashinfer.fused_moe import trtllm_mxint4_block_scale_moe

    assert x.dtype == torch.bfloat16, f"x dtype must be bfloat16, got {x.dtype}"
    assert w13_weight_packed.dtype == torch.uint8, (
        f"w13_weight_packed dtype must be uint8, got {w13_weight_packed.dtype}"
    )
    assert w13_weight_scale.dtype == torch.bfloat16, (
        f"w13_weight_scale dtype must be bfloat16, got {w13_weight_scale.dtype}"
    )
    assert w2_weight_packed.dtype == torch.uint8, (
        f"w2_weight_packed dtype must be uint8, got {w2_weight_packed.dtype}"
    )
    assert w2_weight_scale.dtype == torch.bfloat16, (
        f"w2_weight_scale dtype must be bfloat16, got {w2_weight_scale.dtype}"
    )

    routing_bias = None
    if e_score_correction_bias is not None:
        routing_bias = e_score_correction_bias.to(torch.bfloat16)

    if routing_method_type == RoutingMethodType.DeepSeekV3:
        router_logits = router_logits.to(torch.float32)

    out = trtllm_mxint4_block_scale_moe(
        routing_logits=router_logits,
        routing_bias=routing_bias,
        hidden_states=x,
        gemm1_weights=w13_weight_packed.data,
        gemm1_weights_scale=w13_weight_scale.data,
        gemm1_alpha=None,
        gemm1_beta=None,
        gemm1_clamp_limit=None,
        gemm2_weights=w2_weight_packed.data,
        gemm2_weights_scale=w2_weight_scale.data,
        num_experts=global_num_experts,
        top_k=top_k,
        n_group=num_expert_group if num_expert_group is not None else 0,
        topk_group=topk_group if topk_group is not None else 0,
        intermediate_size=intermediate_size_per_partition,
        local_expert_offset=ep_rank * local_num_experts,
        local_num_experts=local_num_experts,
        routed_scaling_factor=None,
        routing_method_type=routing_method_type,
        enable_pdl=None,
        do_finalize=True,
        output=None,
        tune_max_num_tokens=8192,
    )
    if isinstance(out, (tuple, list)):
        out = out[0]
    out = out.to(x.dtype)

    return out