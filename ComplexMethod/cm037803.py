def prepare_async(
        self,
        a1: torch.Tensor,
        topk_weights: torch.Tensor,
        topk_ids: torch.Tensor,
        num_experts: int,
        expert_map: torch.Tensor | None,
        apply_router_weight_on_input: bool,
        quant_config: FusedMoEQuantConfig,
        defer_input_quant: bool = False,
    ) -> tuple[Callable, mk.ReceiverType]:
        if defer_input_quant:
            raise NotImplementedError(
                f"{self.__class__.__name__} does not support defer_input_quant=True. "
                "Please select an MoE kernel that accepts quantized inputs."
            )

        hidden_size = a1.size(1)
        assert hidden_size in self.SUPPORTED_HIDDEN_SIZES, (
            f"Hidden Size {hidden_size} not in supported list of hidden sizes"
            f"{self.SUPPORTED_HIDDEN_SIZES}"
        )

        a2a_idx = dbo_current_ubatch_id()

        if self.use_fp8_dispatch:
            assert hidden_size % 128 == 0, (
                "DeepEP kernels quantize the inputs in blocks of shape 128"
            )

        use_nvfp4 = False
        nvfp4_dispatch = (
            quant_config.quant_dtype == "nvfp4" and envs.VLLM_DEEPEPLL_NVFP4_DISPATCH
        )
        if nvfp4_dispatch:
            use_nvfp4 = True
        qc_a1_gscale_or_scale = (
            quant_config.a1_gscale if nvfp4_dispatch else quant_config.a1_scale
        )
        has_per_token_scales = (
            qc_a1_gscale_or_scale.numel() != 1
            if qc_a1_gscale_or_scale is not None
            else (
                quant_config.a2_scale.numel() != 1
                if quant_config.a2_scale is not None
                else False
            )
        )
        if not use_nvfp4:
            assert not has_per_token_scales, (
                "low_latency kernels doesn't support dispatching per-token scales"
            )

        if apply_router_weight_on_input:
            topk = topk_ids.size(1)
            # TODO: this only works for topK=1, will need to update for topK>1
            assert topk == 1, (
                "apply_router_weight_on_input is only implemented for topk=1"
            )
            a1 = a1 * topk_weights.to(a1.dtype)

        # Dispatch
        dispatch_topk_ids = self._map_global_to_physical_ids(topk_ids)
        if current_platform.is_rocm():
            (
                expert_x,
                expert_num_tokens,
                handle,
                _,
                hook,
            ) = self.buffer.low_latency_dispatch(
                a1,
                dispatch_topk_ids,
                self.max_tokens_per_rank,
                num_experts,
                use_fp8=self.use_fp8_dispatch,
                async_finish=False,
                return_recv_hook=True,
            )
        else:
            (
                expert_x,
                expert_num_tokens,
                handle,
                _,
                hook,
            ) = self.buffer.low_latency_dispatch(
                a1,
                dispatch_topk_ids,
                self.max_tokens_per_rank,
                num_experts,
                use_fp8=self.use_fp8_dispatch,
                round_scale=self.use_ue8m0_dispatch,
                use_ue8m0=self.use_ue8m0_dispatch,
                **(dict(use_nvfp4=True) if use_nvfp4 else dict()),
                **(
                    dict(x_global_scale=qc_a1_gscale_or_scale)
                    if qc_a1_gscale_or_scale is not None and nvfp4_dispatch
                    else dict()
                ),
                async_finish=False,
                return_recv_hook=True,
            )
        self.handles[a2a_idx] = handle

        return (
            hook,
            lambda: self._receiver(
                expert_x,
                expert_num_tokens,
                quant_config.a1_scale,
                a1.dtype,
                quant_config,
            ),
        )