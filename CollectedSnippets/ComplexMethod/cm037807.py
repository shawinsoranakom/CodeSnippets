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
        if apply_router_weight_on_input:
            topk = topk_ids.size(1)
            assert topk == 1, (
                "apply_router_weight_on_input is only implemented for topk=1"
            )
            a1.mul_(topk_weights.to(a1.dtype))

        global_num_tokens_cpu = get_local_sizes()
        self.runtime_max_tokens_per_rank = (
            max(global_num_tokens_cpu)
            if global_num_tokens_cpu is not None
            else a1.shape[0]
        )

        a1q, a1q_scale = moe_kernel_quantize_input(
            a1,
            quant_config.a1_gscale,
            quant_config.quant_dtype,
            quant_config.per_act_token_quant,
            quant_config.block_shape,
            is_fp4_scale_swizzled=False,  # delay swizzle to after comm
        )

        payloads = []
        payloads.append(a1q)
        if a1q_scale is not None:
            payloads.append(a1q_scale)
        payloads.append(topk_ids)
        payloads.append(topk_weights)

        assert self.all2all_manager.moe_alltoall is not None  # type: ignore[attr-defined]
        recv_payloads = self.all2all_manager.moe_alltoall.dispatch(  # type: ignore[attr-defined]
            token_selected_experts=topk_ids,
            input_payloads=payloads,
            runtime_max_tokens_per_rank=self.runtime_max_tokens_per_rank,
        )
        if a1q_scale is not None:
            a1q_recv, a1q_scale_recv, topk_ids_recv, topk_weights_recv = recv_payloads
            # Apply scale interleaving only for CUTLASS (not TRT-LLM)
            if (
                quant_config.quant_dtype == "nvfp4"
                and quant_config.is_nvfp4_scale_swizzled
            ):
                a1q_scale_recv = a1q_scale_recv.view(-1, a1q_scale_recv.shape[-1])
                a1q_scale_recv = a1q_scale_recv.view(torch.uint8)
                a1q_scale_recv = nvfp4_block_scale_interleave(a1q_scale_recv)
            a1q_scale_recv = a1q_scale_recv.view(-1, self.hidden_size // 16)
        else:
            a1q_recv, topk_ids_recv, topk_weights_recv = recv_payloads
            a1q_scale_recv = None
        a1q_recv = a1q_recv.view(-1, a1q_recv.shape[-1])
        topk_ids_recv = topk_ids_recv.view(-1, topk_ids_recv.shape[-1])
        topk_weights_recv = topk_weights_recv.view(-1, topk_weights_recv.shape[-1])

        return a1q_recv, a1q_scale_recv, None, topk_ids_recv, topk_weights_recv