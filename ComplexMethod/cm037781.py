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
        # Check constraints.
        if self.quant_config.use_int4_w4a16:
            assert hidden_states.size(-1) // 2 == w1.size(2), "Hidden size mismatch"
        else:
            assert hidden_states.size(-1) == w1.size(2), (
                f"Hidden size mismatch {hidden_states.size(-1)} != {w1.size(2)}"
            )

        assert hidden_states.is_contiguous(), "Hidden_states must be contiguous"
        assert w1.stride(-1) == 1, "Stride of last dimension must be 1"
        assert w2.stride(-1) == 1, "Stride of last dimension must be 1"
        assert hidden_states.dtype in [
            torch.float32,
            torch.float16,
            torch.bfloat16,
            torch.float8_e4m3fn,
            torch.float8_e4m3fnuz,
        ]
        assert expert_tokens_meta is not None

        expert_num_tokens = expert_tokens_meta.expert_num_tokens

        E, max_num_tokens, N, K, top_k_num = self.moe_problem_size(
            hidden_states, w1, w2, topk_ids
        )

        assert w1.size(0) == E
        assert w2.size(0) == E

        config_dtype = self.quant_config.config_name(hidden_states.dtype)

        config = try_get_optimal_moe_config(
            w1.size(),
            w2.size(),
            top_k_num,
            config_dtype,
            max_num_tokens,
            block_shape=self.block_shape,
        )

        if hidden_states.dtype == torch.bfloat16:
            compute_type = tl.bfloat16
        elif hidden_states.dtype == torch.float16:
            compute_type = tl.float16
        elif hidden_states.dtype == torch.float32:
            compute_type = tl.float32
        elif hidden_states.dtype == current_platform.fp8_dtype():
            compute_type = tl.bfloat16
        else:
            raise ValueError(f"Unsupported compute_type: {hidden_states.dtype}")

        # We can reuse the memory between these because by the time we need
        # cache3, we're done with cache1
        intermediate_cache1 = _resize_cache(workspace13, (E, max_num_tokens, N))
        activation_out_dim = self.adjust_N_for_activation(N, activation)
        intermediate_cache2 = _resize_cache(
            workspace2, (E, max_num_tokens, activation_out_dim)
        )

        # TODO(bnell): should this be done for any quantized type?
        if self.quant_config.use_fp8_w8a8:
            intermediate_cache1.fill_(0)

        a1q_scale = normalize_batched_scales_shape(a1q_scale, E)

        # MM1
        invoke_moe_batched_triton_kernel(
            A=hidden_states,
            B=w1,
            C=intermediate_cache1,
            expert_num_tokens=expert_num_tokens,
            compute_type=compute_type,
            A_scale=a1q_scale,
            B_scale=self.w1_scale,
            B_zp=self.w1_zp,
            use_fp8_w8a8=self.quant_config.use_fp8_w8a8,
            use_int8_w8a16=self.quant_config.use_int8_w8a16,
            use_int4_w4a16=self.quant_config.use_int4_w4a16,
            config=config,
            per_act_token_quant=self.per_act_token_quant,
            block_shape=self.block_shape,
        )

        intermediate_cache2.fill_(0)

        # TODO (bnell): use triton utility from batched deep gemm.
        self.activation(
            activation,
            intermediate_cache2.view(-1, activation_out_dim),
            intermediate_cache1.view(-1, N),
        )

        qintermediate_cache2, a2q_scale = batched_moe_kernel_quantize_input(
            intermediate_cache2,
            a2_scale,
            max_num_tokens,
            E,
            N,
            expert_num_tokens,
            self.quant_dtype,
            self.per_act_token_quant,
            self.block_shape,
        )

        invoke_moe_batched_triton_kernel(
            A=qintermediate_cache2,
            B=w2,
            C=output,
            expert_num_tokens=expert_num_tokens,
            compute_type=compute_type,
            A_scale=a2q_scale,
            B_scale=self.w2_scale,
            B_zp=self.w2_zp,
            use_fp8_w8a8=self.quant_config.use_fp8_w8a8,
            use_int8_w8a16=self.quant_config.use_int8_w8a16,
            use_int4_w4a16=self.quant_config.use_int4_w4a16,
            config=config,
            per_act_token_quant=self.per_act_token_quant,
            block_shape=self.block_shape,
        )