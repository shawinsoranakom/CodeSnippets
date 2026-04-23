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
        a2_scale: torch.Tensor | None,  # Not used
        workspace13: torch.Tensor | None,
        workspace2: torch.Tensor | None,
        expert_tokens_meta: mk.ExpertTokensMetadata | None,
        apply_router_weight_on_input: bool | None,
    ):
        assert self.quant_dtype == "nvfp4", (
            "Only nvfp4 quantization are currently supported."
        )
        # Ensure w1_scale and w2_scale are not None before calling view
        assert self.w1_scale is not None and self.w2_scale is not None, (
            "w1_scale and w2_scale must not be None for FlashInferExperts"
        )
        assert expert_tokens_meta is not None
        expert_num_tokens = expert_tokens_meta.expert_num_tokens
        assert hidden_states.ndim == 3
        assert self.w1_scale.ndim == 3
        assert self.w2_scale.ndim == 3

        input_global_scale = (
            None if envs.VLLM_DEEPEPLL_NVFP4_DISPATCH else self.a1_gscale
        )
        flashinfer_hidden_states = (
            (hidden_states, a1q_scale)
            if envs.VLLM_DEEPEPLL_NVFP4_DISPATCH
            else hidden_states
        )
        flashinfer_cutedsl_moe_masked(
            hidden_states=flashinfer_hidden_states,
            input_global_scale=input_global_scale,
            w1=w1,
            w1_blockscale=self.w1_scale,
            w1_alpha=self.g1_alphas,
            w2=w2,
            a2_global_scale=self.a2_gscale,
            w2_blockscale=self.w2_scale,
            w2_alpha=self.g2_alphas,
            masked_m=expert_num_tokens,
            workspace=workspace2,
            out=output,
        )