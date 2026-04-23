def fused_topk_bias(
    hidden_states: torch.Tensor,
    gating_output: torch.Tensor,
    e_score_correction_bias: torch.Tensor,
    topk: int,
    renormalize: bool,
    scoring_func: str = "softmax",
    indices_type: torch.dtype | None = None,
):
    if not rocm_aiter_ops.is_fused_moe_enabled():
        assert hidden_states.size(0) == gating_output.size(0), (
            "Number of tokens mismatch"
        )

        M, _ = hidden_states.size()

        topk_weights = torch.empty(
            M, topk, dtype=torch.float32, device=hidden_states.device
        )
        topk_ids = torch.empty(
            M,
            topk,
            dtype=torch.int32 if indices_type is None else indices_type,
            device=hidden_states.device,
        )
        token_expert_indices = torch.empty(
            M, topk, dtype=torch.int32, device=hidden_states.device
        )

        if scoring_func == "softmax":
            topk_weights, topk_ids = vllm_topk_softmax(
                topk_weights,
                topk_ids,
                token_expert_indices,
                gating_output,
                renormalize,
                e_score_correction_bias,
            )
            return topk_weights, topk_ids
        elif scoring_func == "sigmoid":
            topk_weights, topk_ids = vllm_topk_sigmoid(
                topk_weights,
                topk_ids,
                token_expert_indices,
                gating_output,
                renormalize,
                e_score_correction_bias,
            )
            return topk_weights, topk_ids
        else:
            raise ValueError(f"Unsupported scoring function: {scoring_func}")
    elif rocm_aiter_ops.is_fused_moe_enabled() and scoring_func == "sigmoid":
        M = hidden_states.size(0)
        num_experts = gating_output.shape[-1]
        num_expert_group = _aiter_get_num_expert_group(num_experts)
        if topk >= num_expert_group:
            topk_weights = torch.empty(
                M, topk, dtype=torch.float32, device=hidden_states.device
            )
            topk_ids = torch.empty(
                M,
                topk,
                dtype=torch.int32 if indices_type is None else indices_type,
                device=hidden_states.device,
            )
            rocm_aiter_ops.biased_grouped_topk(
                gating_output,
                e_score_correction_bias.to(gating_output.dtype),
                topk_weights,
                topk_ids,
                num_expert_group=num_expert_group,
                topk_group=num_expert_group,
                need_renorm=renormalize,
            )
            return topk_weights, topk_ids

    n_routed_experts = gating_output.shape[-1]
    if scoring_func == "softmax":
        scores = gating_output.softmax(dim=-1)
    elif scoring_func == "sigmoid":
        scores = gating_output.sigmoid()
    else:
        raise ValueError(f"Unsupported scoring function: {scoring_func}")

    scores_for_choice = scores.view(
        -1, n_routed_experts
    ) + e_score_correction_bias.unsqueeze(0)

    # For batch invariance, use sorted=True to ensure deterministic expert selection
    use_sorted = envs.VLLM_BATCH_INVARIANT
    topk_indices = torch.topk(scores_for_choice, k=topk, dim=-1, sorted=use_sorted)[1]
    topk_weights = scores.gather(1, topk_indices)
    if renormalize:
        topk_weights = topk_weights / topk_weights.sum(dim=-1, keepdim=True)
    return topk_weights.to(torch.float32), topk_indices.to(
        torch.int32 if indices_type is None else indices_type
    )