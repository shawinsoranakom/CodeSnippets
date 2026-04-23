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
        assert hidden_states.dim() == 3
        assert expert_tokens_meta is not None
        expert_num_tokens = expert_tokens_meta.expert_num_tokens

        num_local_experts = w1.size(0)
        assert num_local_experts == w1.size(0), f"{num_local_experts} == {w1.size(0)}"

        N = w1.size(1) // 2

        for expert in range(num_local_experts):
            # Indexing expert_num_tokens doesn't work w/cudagraphs or inductor
            if (
                torch.compiler.is_compiling()
                or torch.cuda.is_current_stream_capturing()
            ):
                num = hidden_states.shape[1]
            else:
                num = int(expert_num_tokens[expert].item())

            if num == 0:
                continue

            tmp = _resize_cache(workspace2, (num, N))

            if self.quant_config.is_quantized:
                assert a1q_scale is not None and self.w1_scale is not None
                input = self.dequant(hidden_states[expert, :, :], a1q_scale[expert])
                w1_dq = self.dequant(w1[expert], self.w1_scale[expert])
                input = input[:num] @ w1_dq.transpose(0, 1)
            else:
                input = hidden_states[expert, :num, :] @ w1[expert].transpose(0, 1)

            self.activation(activation, tmp, input.to(tmp.dtype))

            if self.quant_config.is_quantized:
                assert self.w2_scale is not None
                w2_dq = self.dequant(w2[expert], self.w2_scale[expert])
            else:
                w2_dq = w2[expert]

            output[expert, :num, :] = tmp @ w2_dq.transpose(0, 1).to(tmp.dtype)