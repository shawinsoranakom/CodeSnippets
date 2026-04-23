def prepare(
        self,
        a1: torch.Tensor,
        topk_weights: torch.Tensor,
        topk_ids: torch.Tensor,
        num_experts: int,
        expert_map: torch.Tensor | None,
        apply_router_weight_on_input: bool,
        quant_config: FusedMoEQuantConfig,
        defer_input_quant: bool = False,
    ) -> mk.PrepareResultType:
        if defer_input_quant:
            raise NotImplementedError(
                f"{self.__class__.__name__} does not support defer_input_quant=True. "
                "Please select an MoE kernel that accepts quantized inputs."
            )
        assert a1.dim() == 2
        assert topk_ids.dim() == 2
        assert topk_ids.size(0) == a1.size(0)

        if apply_router_weight_on_input:
            topk = topk_ids.size(1)
            # TODO: this only works for topK=1, will need to update for topK>1
            assert topk == 1, (
                "apply_router_weight_on_input is only implemented for topk=1"
            )
            a1.mul_(topk_weights.to(a1.dtype))

        num_tokens, hidden_dim = a1.size()
        topk = topk_ids.size(1)

        tokens_per_expert = torch.zeros(num_experts, dtype=torch.int, device=a1.device)

        num_local_experts = self.num_local_experts

        if quant_config.quant_dtype is None:
            b_type = a1.dtype
        else:
            b_type = quant_config.quant_dtype

        b_a1 = torch.zeros(
            (num_local_experts, self.max_num_tokens, hidden_dim),
            dtype=b_type,
            device=a1.device,
        )

        if quant_config.is_quantized:
            scale_shape = quant_config.batched_scale_shape(
                num_local_experts, self.max_num_tokens, hidden_dim
            )

            b_a1_scale = torch.empty(scale_shape, dtype=torch.float32, device=a1.device)
        else:
            assert quant_config.a1_scale is None
            b_a1_scale = None

        first_expert = num_local_experts * self.rank
        last_expert = first_expert + num_local_experts

        a1_scale = normalize_scales_shape(quant_config.a1_scale)

        for expert_id in range(first_expert, last_expert):
            topks = torch.any(topk_ids == expert_id, dim=1).flatten()
            rows = torch.count_nonzero(topks.flatten())
            if rows == 0:
                continue
            idx = expert_id - first_expert
            tokens_per_expert[idx] = rows
            rhs = a1[: topks.numel()][topks]
            if quant_config.quant_dtype is not None:
                if a1_scale is not None:
                    if quant_config.is_per_act_token:
                        rhs_a1_scale = a1_scale[: topks.numel()][topks]
                    else:
                        rhs_a1_scale = a1_scale
                else:
                    rhs_a1_scale = None
                b_a1[idx, :rows, :], b_s = moe_kernel_quantize_input(
                    rhs,
                    rhs_a1_scale,
                    quant_config.quant_dtype,
                    quant_config.per_act_token_quant,
                    quant_config.block_shape,
                )
                assert b_s is not None
                if quant_config.is_per_act_token:
                    b_a1_scale[idx, :rows] = b_s[:rows]
                else:
                    b_a1_scale[idx, : b_s.shape[0]] = b_s
            else:
                b_a1[idx, :rows, :] = rhs

        assert b_a1_scale is None or b_a1_scale.ndim == 3

        expert_tokens_meta = mk.ExpertTokensMetadata(
            expert_num_tokens=tokens_per_expert, expert_num_tokens_cpu=None
        )

        return b_a1, b_a1_scale, expert_tokens_meta, None, None