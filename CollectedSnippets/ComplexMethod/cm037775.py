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
        workspace13: torch.Tensor | None,
        workspace2: torch.Tensor | None,
        expert_tokens_meta: mk.ExpertTokensMetadata | None,
        apply_router_weight_on_input: bool | None,
    ):
        from flashinfer.fused_moe.core import ActivationType

        activation_str_to_value_map = {
            MoEActivation.SILU: ActivationType.Swiglu,  # This is the default
            MoEActivation.SWIGLUOAI: ActivationType.Swiglu,  # gpt-oss alias
            MoEActivation.RELU2_NO_MUL: ActivationType.Relu2,
        }
        assert activation in activation_str_to_value_map, (
            f"{activation=} missing from {activation_str_to_value_map.keys()=}"
        )

        quant_scales = None
        fc1_expert_weights = None
        fc2_expert_weights = None
        fc1_expert_biases = None
        fc2_expert_biases = None
        swiglu_alpha = None
        swiglu_beta = None
        swiglu_limit = None
        use_mxfp8_act_scaling = False
        use_w4_group_scaling = False
        # Select quantization metadata based on FP8 format/path
        if (
            self.quant_dtype == torch.float8_e4m3fn
            and not self.use_deepseek_fp8_block_scale
        ):
            # FP8 per-tensor path: use global alphas/scales; do not pass input_sf
            quant_scales = [
                self.g1_alphas,  # w13_weight_scale * w13_input_scale
                self.a2_gscale,  # 1.0 / w2_input_scale
                self.g2_alphas,  # w2_weight_scale * w2_input_scale
                self.a1_scale,
            ]

            a1q_scale = None  # not passing input_sf in fp8
            fc1_expert_weights = w1
            fc2_expert_weights = w2
        elif self.quant_dtype == "nvfp4":
            # Ensure w1_scale and w2_scale are not None before calling view
            assert self.w1_scale is not None and self.w2_scale is not None, (
                "w1_scale and w2_scale must not be None for FlashInferExperts"
            )
            # Flashinfer CUTLASS kernel takes scalar global scales,
            # min because inv_scale.
            quant_scales = [
                self.a1_gscale,
                self.w1_scale.view(torch.int32),
                self.g1_alphas,
                self.a2_gscale,
                self.w2_scale.view(torch.int32),
                self.g2_alphas,
            ]
            # FlashInfer API requires weight to be long for nvfp4
            fc1_expert_weights = w1.view(torch.long)
            fc2_expert_weights = w2.view(torch.long)
        elif self.weight_quant_dtype == "mxfp4":
            assert self.w1_scale is not None and self.w2_scale is not None
            assert w1.is_contiguous() and w2.is_contiguous()
            assert self.gemm1_alpha is not None
            assert self.gemm1_beta is not None
            assert self.gemm1_clamp_limit is not None
            assert topk_ids.is_contiguous()

            fc1_expert_biases = self.w1_bias
            fc2_expert_biases = self.w2_bias
            swiglu_alpha = self.gemm1_alpha
            swiglu_beta = self.gemm1_beta
            swiglu_limit = self.gemm1_clamp_limit

            if self.quant_dtype == "mxfp8":
                assert self.fake_input_scale is not None
                fc1_expert_weights = w1.view(torch.long)
                fc2_expert_weights = w2.view(torch.long)

                quant_scales = [
                    self.w1_scale.view(torch.int32),
                    self.fake_input_scale,
                    self.w2_scale.view(torch.int32),
                    self.fake_input_scale,
                ]
                use_mxfp8_act_scaling = True
            else:
                assert hidden_states.dtype == torch.bfloat16
                fc1_expert_weights = w1
                fc2_expert_weights = w2
                quant_scales = [
                    self.w1_scale,
                    self.w2_scale,
                ]
                a1q_scale = None
                use_w4_group_scaling = True

        elif self.use_deepseek_fp8_block_scale:
            # FP8 block-scale path: provide block-scale weights, omit a1q_scale
            quant_scales = [
                self.w1_scale,
                self.w2_scale,
            ]
            a1q_scale = None
            fc1_expert_weights = w1
            fc2_expert_weights = w2
        else:
            quant_scales = []
            a1q_scale = None
            fc1_expert_weights = w1
            fc2_expert_weights = w2

        _ = flashinfer_cutlass_fused_moe(
            input=hidden_states,
            token_selected_experts=topk_ids.to(torch.int),
            token_final_scales=topk_weights,
            fc1_expert_weights=fc1_expert_weights,
            fc2_expert_weights=fc2_expert_weights,
            fc1_expert_biases=fc1_expert_biases,
            fc2_expert_biases=fc2_expert_biases,
            swiglu_alpha=swiglu_alpha,
            swiglu_beta=swiglu_beta,
            swiglu_limit=swiglu_limit,
            output=output,
            output_dtype=self.out_dtype,
            quant_scales=quant_scales,
            input_sf=a1q_scale,
            tp_size=self.tp_size,
            tp_rank=self.tp_rank,
            ep_size=self.ep_size,
            ep_rank=self.ep_rank,
            activation_type=activation_str_to_value_map[activation],
            # Informs FlashInfer to use the block-scale decoding path when True
            use_deepseek_fp8_block_scale=self.use_deepseek_fp8_block_scale,
            use_mxfp8_act_scaling=use_mxfp8_act_scaling,
            use_w4_group_scaling=use_w4_group_scaling,
            tune_max_num_tokens=max(self.max_capture_size, 1),
        )