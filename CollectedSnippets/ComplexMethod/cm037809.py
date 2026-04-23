def triton_kernel_fused_experts(
    output_tensor: torch.Tensor,
    hidden_states: torch.Tensor,
    w1,  # Tensor or triton_kernels.Tensor
    w2,  # Tensor or triton_kernels.Tensor
    routing_data,  # RoutingData
    gather_indx,  # GatherIndx
    scatter_indx,  # ScatterIndx
    topk: int,
    activation: MoEActivation = MoEActivation.SWIGLUOAI,
    quant_config: FusedMoEQuantConfig | None = None,
    swiglu_alpha: float = 1.702,
    swiglu_limit: float = 7.0,
    apply_router_weight_on_input: bool = False,
    global_num_experts: int = -1,
    expert_map: torch.Tensor | None = None,
    intermediate_cache: torch.Tensor | None = None,
    a1q_scale: torch.Tensor | None = None,
) -> torch.Tensor:
    """Triton implementation of fused expert computation using OAI kernels."""
    assert activation == MoEActivation.SWIGLUOAI, (
        "Only SWIGLUOAI activation is supported"
    )
    assert quant_config is not None

    # type check, uint8 means mxfp4
    assert hidden_states.dtype == torch.bfloat16
    assert quant_config.w1_bias is None or quant_config.w1_bias.dtype == torch.float32
    assert quant_config.w2_bias is None or quant_config.w2_bias.dtype == torch.float32

    # Shape check, only check non-mxfp4
    assert hidden_states.ndim == 2
    assert hidden_states.shape[-1] == w1.shape[-2]
    assert w2.shape[-1] == w1.shape[1]

    batch_dim = 1
    M, K = hidden_states.shape[-2:]
    E, _, N = w1.shape

    if global_num_experts == -1:
        global_num_experts = E

    if intermediate_cache is None:
        intermediate_cache = torch.empty(
            (batch_dim, M * topk, N // 2),
            device=hidden_states.device,
            dtype=hidden_states.dtype,
        )

    # Add batch_dim to output buffer because matmul_ogs expects 3D output
    intermediate_cache = _resize_cache(
        intermediate_cache, (batch_dim, M * topk, N // 2)
    )
    output_tensor = _resize_cache(output_tensor, (batch_dim, M, K))

    act = (
        FusedActivation(
            FnSpecs(
                "swiglu",
                triton_kernels.swiglu.swiglu_fn,
                ("alpha", "limit"),
                reduction_n=2,
            ),
            (swiglu_alpha, swiglu_limit),
        )
        if not use_legacy_triton_kernels
        else FusedActivation(
            FnSpecs("swiglu", triton_kernels.swiglu.swiglu_fn, ("alpha", "limit")),
            (swiglu_alpha, swiglu_limit),
            2,
        )
    )
    gammas = routing_data.gate_scal if routing_data else None

    matmul_ogs(
        hidden_states,
        w1,
        quant_config.w1_bias,
        routing_data,
        gather_indx=gather_indx,
        precision_config=quant_config.w1_precision,
        gammas=gammas if apply_router_weight_on_input else None,
        fused_activation=act,
        y=intermediate_cache,
    )

    matmul_ogs(
        intermediate_cache.view(M * topk, N // 2),
        w2,
        quant_config.w2_bias,
        routing_data,
        scatter_indx=scatter_indx,
        precision_config=quant_config.w2_precision,
        gammas=None if apply_router_weight_on_input else gammas,
        y=output_tensor,
    )
    output_tensor = output_tensor.view(M, K)
    return output_tensor