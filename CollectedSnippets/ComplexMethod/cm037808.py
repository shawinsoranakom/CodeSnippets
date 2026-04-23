def triton_kernel_moe_forward(
    hidden_states: torch.Tensor,
    w1,  # Tensor or triton_kernels.Tensor
    w2,  # Tensor or triton_kernels.Tensor
    gating_output: torch.Tensor,
    topk: int,
    renormalize: bool,
    activation: MoEActivation = MoEActivation.SWIGLUOAI,
    quant_config: FusedMoEQuantConfig | None = None,
    apply_router_weight_on_input: bool = False,
    global_num_experts: int = -1,
    expert_map: torch.Tensor | None = None,
    unpadded_N_w1=None,
    unpadded_K_w1=None,
    unpadded_N_w2=None,
    unpadded_K_w2=None,
) -> torch.Tensor:
    if (
        quant_config is not None
        and quant_config.use_mxfp4_w4a8
        and rocm_aiter_ops.is_enabled()
    ):
        from aiter.ops.triton.moe_routing.routing import routing as aiter_routing

        routing_data, gather_idx, scatter_idx = aiter_routing(
            gating_output, topk, sm_first=not renormalize
        )
        return triton_kernel_fused_mxfp4_w4a8_experts(
            None,
            hidden_states,
            w1,
            w2,
            routing_data,
            gather_idx,
            scatter_idx,
            activation=activation.value,
            quant_config=quant_config,
            apply_router_weight_on_input=apply_router_weight_on_input,
            global_num_experts=global_num_experts,
            expert_map=expert_map,
            unpadded_N_w1=unpadded_N_w1,
            unpadded_K_w1=unpadded_K_w1,
            unpadded_N_w2=unpadded_N_w2,
            unpadded_K_w2=unpadded_K_w2,
        )

    from triton_kernels.topk import topk as topk_fn

    sm_first = not renormalize
    logits = gating_output
    if sm_first:
        logits = torch.softmax(logits, dim=-1)
    topk_result = topk_fn(logits, topk, apply_softmax=not sm_first)
    # topk may return a tuple (vals, indx, bitmatrix) or a
    # SparseMatrix depending on the triton_kernels version.
    if isinstance(topk_result, tuple):
        topk_weights, topk_ids_raw, _ = topk_result
    else:
        topk_weights = topk_result.vals
        topk_ids_raw = topk_result.indx

    if expert_map is not None:
        # topk_ids_raw contains global expert IDs - remap to local.
        topk_ids = expert_map[topk_ids_raw.to(torch.long)]
        local_num_experts = w1.shape[0]
        routing_data, gather_idx, scatter_idx = make_routing_data(
            topk_ids, topk_weights, local_num_experts
        )
        # expert_map already applied; pass None downstream.
        effective_expert_map = None
        effective_global_num_experts = local_num_experts
    else:
        topk_ids = topk_ids_raw.to(torch.long)
        routing_data, gather_idx, scatter_idx = make_routing_data(
            topk_ids, topk_weights, gating_output.shape[-1]
        )
        effective_expert_map = expert_map
        effective_global_num_experts = global_num_experts

    output = torch.empty_like(hidden_states)
    effective_quant_config = (
        quant_config if quant_config is not None else FUSED_MOE_UNQUANTIZED_CONFIG
    )

    return triton_kernel_fused_experts(
        output,
        hidden_states,
        w1,
        w2,
        routing_data,
        gather_idx,
        scatter_idx,
        topk=topk,
        activation=activation,
        quant_config=effective_quant_config,
        apply_router_weight_on_input=apply_router_weight_on_input,
        global_num_experts=effective_global_num_experts,
        expert_map=effective_expert_map,
    )