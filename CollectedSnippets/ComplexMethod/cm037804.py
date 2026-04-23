def _receiver(
        self,
        event: deep_ep.EventOverlap,
        has_scales: bool,
        token_data: tuple[torch.Tensor, torch.Tensor] | torch.Tensor,
        expert_topk_ids: torch.Tensor | None,
        num_experts: int,
        expert_num_tokens_per_expert_list: list[int],
        expert_topk_weights: torch.Tensor | None,
        a1_scale: torch.Tensor | None,
        quant_config: FusedMoEQuantConfig,
        defer_input_quant: bool,
    ) -> mk.PrepareResultType:
        if event.event is not None:
            event.current_stream_wait()

        if has_scales:
            expert_x, expert_x_scale = token_data
        else:
            expert_x, expert_x_scale = token_data, None

        # The existing MOE kernels assume that all entries of topk_ids are
        # valid. To that effect, set the -1s in expert_topk_ids to some expert
        # outside this rank so the expert_map can remap it to -1 when safe.
        # With Expert Parallel, the experts are divided amongst the rank
        # sequentially. For rank 0, set it to num_experts - 1 and for all other
        # ranks set it to 0 as we know that expert_map will have a -1 in those
        # regions for those ranks.
        #
        # DeepEP's topk_ids output refers to the local experts directly. Offset
        # the topk_ids to move it back to the global experts space so it aligns
        # with existing vLLM interfaces.
        assert expert_topk_ids is not None
        expert_topk_ids = torch.where(
            expert_topk_ids == -1,
            num_experts - 1 if self.rank_expert_offset == 0 else 0,
            expert_topk_ids + self.rank_expert_offset,
        )

        # Makes a GPU-CPU copy.
        # TODO (varun): Maybe it is better to re-compute the expert_num_tokens
        # on GPU.
        expert_tokens_meta = mk.ExpertTokensMetadata.make_from_list(
            expert_num_tokens_per_expert_list, device=expert_x.device
        )

        # * For non-block quant, dispatch in b16 and quantize now as
        #   DeepEP kernels only support dispatching block scales.
        # * For expert kernels that require unquantized inputs,
        #   defer quantization to FusedMoEExpertsPermuteUnpermute.
        if not quant_config.is_block_quantized and not defer_input_quant:
            # Quantize after dispatch.
            expert_x_scale = None
            if expert_x.numel() != 0:
                # TODO: support per_act_token_quant,
                expert_x, expert_x_scale = moe_kernel_quantize_input(
                    expert_x,
                    a1_scale,
                    quant_dtype=quant_config.quant_dtype,
                    per_act_token_quant=False,
                    block_shape=quant_config.block_shape,
                    is_fp4_scale_swizzled=quant_config.is_nvfp4_scale_swizzled,
                )

        return (
            expert_x,
            expert_x_scale,
            expert_tokens_meta,
            expert_topk_ids,
            expert_topk_weights,
        )