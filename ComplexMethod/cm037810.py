def triton_kernel_fused_mxfp4_w4a8_experts(
    output_tensor: torch.Tensor,
    hidden_states: torch.Tensor,
    w1,  # Tensor or triton_kernels.Tensor
    w2,  # Tensor or triton_kernels.Tensor
    routing_data,  # RoutingData
    gather_indx,  # GatherIndx
    scatter_indx,  # ScatterIndx
    activation: str = "silu",
    quant_config: FusedMoEQuantConfig | None = None,
    swiglu_alpha: float = 1.702,
    swiglu_limit: float = 7.0,
    apply_router_weight_on_input: bool = False,
    global_num_experts: int = -1,
    expert_map: torch.Tensor | None = None,
    a1q_scale: torch.Tensor | None = None,
    unpadded_N_w1=None,
    unpadded_K_w1=None,
    unpadded_N_w2=None,
    unpadded_K_w2=None,
) -> torch.Tensor:
    assert quant_config is not None
    # type check, uint8 means mxfp4
    assert hidden_states.dtype == torch.bfloat16
    assert quant_config.w1_bias is None or quant_config.w1_bias.dtype == torch.float32
    assert quant_config.w2_bias is None or quant_config.w2_bias.dtype == torch.float32

    # Shape check: weights are padded (e.g. hidden_size padded for
    # GFX950 swizzle).
    assert hidden_states.shape[-1] == w1.shape[-2]
    assert w2.shape[-1] == w1.shape[1]

    E, _, N = w1.shape

    if global_num_experts == -1:
        global_num_experts = E

    gammas = routing_data.gate_scal if routing_data else None

    from aiter.ops.triton.moe_op_gemm_a8w4 import moe_gemm_a8w4
    from aiter.ops.triton.quant_moe import downcast_to_static_fp8

    assert quant_config.w1_precision is not None, (
        "w1_precision in quant config can't be None"
    )
    assert quant_config.w2_precision is not None, (
        "w2_precision in quant config can't be None"
    )

    hidden_states = downcast_to_static_fp8(
        hidden_states, quant_config.w1_precision.flex_ctx.lhs_data.scale
    )

    intermediate_cache1 = moe_gemm_a8w4(
        hidden_states,
        w1.storage.data,
        None,
        quant_config.w1_precision.weight_scale.storage.data,
        quant_config.w1_precision.flex_ctx.lhs_data.scale,
        quant_config.w2_precision.flex_ctx.lhs_data.scale,
        quant_config.w1_bias,
        routing_data,
        gather_indx=gather_indx,
        gammas=gammas if apply_router_weight_on_input else None,
        swizzle_mx_scale="CDNA4_SCALE",
        out_dtype=torch.float8_e4m3fn,
        apply_swiglu=True,
        alpha=swiglu_alpha,
        limit=swiglu_limit,
        unpadded_N=unpadded_N_w1,
        unpadded_K=unpadded_K_w1,
    )

    intermediate_cache3 = moe_gemm_a8w4(
        intermediate_cache1,
        w2.storage.data,
        None,
        quant_config.w2_precision.weight_scale.storage.data,
        quant_config.w2_precision.flex_ctx.lhs_data.scale,
        None,
        quant_config.w2_bias,
        routing_data,
        scatter_indx=scatter_indx,
        gammas=None if apply_router_weight_on_input else gammas,
        swizzle_mx_scale="CDNA4_SCALE",
        unpadded_N=unpadded_N_w2,
        unpadded_K=unpadded_K_w2,
    )

    return intermediate_cache3