def apply(
        self,
        output: torch.Tensor,
        hidden_states: torch.Tensor,
        w1: torch.Tensor,
        w2: torch.Tensor,
        topk_weights: torch.Tensor,
        topk_ids: torch.Tensor,
        activation: MoEActivation,
        global_num_experts: int,
        expert_map: torch.Tensor | None,
        a1q_scale: torch.Tensor | None,
        a2_scale: torch.Tensor | None,
        workspace13: torch.Tensor,
        workspace2: torch.Tensor,
        expert_tokens_meta: mk.ExpertTokensMetadata | None,
        apply_router_weight_on_input: bool,
    ):
        assert a1q_scale is not None
        assert a2_scale is None
        assert self.block_shape is not None
        assert self.w1_scale is not None
        assert self.w2_scale is not None

        a1q = hidden_states
        _, N, K = w1.size()

        local_num_experts = w1.size(0)
        if global_num_experts == -1:
            global_num_experts = local_num_experts

        assert w2.size(1) == K

        M_sum = compute_aligned_M(
            M=topk_ids.size(0),
            num_topk=topk_ids.size(1),
            local_num_experts=local_num_experts,
            alignment=get_mk_alignment_for_contiguous_layout()[0],
            expert_tokens_meta=expert_tokens_meta,
        )

        a1q_perm = _resize_cache(
            workspace13.view(dtype=torch.float8_e4m3fn), (M_sum, K)
        )
        a1q, a1q_scale, expert_ids, inv_perm = deepgemm_moe_permute(
            aq=a1q,
            aq_scale=a1q_scale,
            topk_ids=topk_ids,
            local_num_experts=local_num_experts,
            expert_map=expert_map,
            expert_tokens_meta=expert_tokens_meta,
            aq_out=a1q_perm,
        )
        assert a1q.size(0) == M_sum

        mm1_out = _resize_cache(workspace2, (M_sum, N))
        m_grouped_fp8_gemm_nt_contiguous(
            (a1q, a1q_scale), (w1, self.w1_scale), mm1_out, expert_ids
        )

        activation_out_dim = self.adjust_N_for_activation(N, activation)
        quant_out = _resize_cache(
            workspace13.view(dtype=torch.float8_e4m3fn), (M_sum, activation_out_dim)
        )
        a2q, a2q_scale = self._act_mul_quant(
            input=mm1_out.view(-1, N), output=quant_out, activation=activation
        )

        mm2_out = _resize_cache(workspace2, (M_sum, K))
        m_grouped_fp8_gemm_nt_contiguous(
            (a2q, a2q_scale), (w2, self.w2_scale), mm2_out, expert_ids
        )

        if apply_router_weight_on_input:
            topk_weights = torch.ones_like(topk_weights)

        deepgemm_unpermute_and_reduce(
            a=mm2_out,
            topk_ids=topk_ids,
            topk_weights=topk_weights,
            inv_perm=inv_perm,
            expert_map=expert_map,
            output=output,
        )