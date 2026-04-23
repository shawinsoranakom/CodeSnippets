def _apply_8bit_weight(
        self,
        layer: torch.nn.Module,
        x: torch.Tensor,
        bias: torch.Tensor | None = None,
    ) -> torch.Tensor:
        # only load the bitsandbytes module when needed
        from bitsandbytes import MatmulLtState, matmul

        original_type = x.dtype
        original_shape = x.shape
        reshape_after_matmul = False
        if x.ndim > 2:
            x = x.reshape(-1, x.size(-1))
            reshape_after_matmul = True
        bf_x = x.to(torch.bfloat16)

        qweight = layer.weight
        offsets = qweight.bnb_shard_offsets
        quant_states = qweight.bnb_quant_state
        matmul_states = qweight.matmul_state
        generation = qweight.generation

        out_dim_0 = x.shape[0]
        out_dim_1 = sum(
            [quant_state[1].shape[0] for quant_state in quant_states.items()]
        )
        out = torch.empty(out_dim_0, out_dim_1, dtype=torch.float16, device=x.device)

        current_index = 0
        for i in range(len(quant_states)):
            output_size = quant_states[i].shape[0]

            # in profile_run or the first generation of inference,
            # create new matmul_states
            if generation == 0 or generation == 1:
                matmul_states[i] = MatmulLtState()
                matmul_states[i].CB = qweight[offsets[i] : offsets[i + 1]]
                matmul_states[i].SCB = quant_states[i].to(x.device)
                matmul_states[i].threshold = self.quant_config.llm_int8_threshold
                matmul_states[
                    i
                ].has_fp16_weights = self.quant_config.llm_int8_has_fp16_weight
                matmul_states[i].is_training = False
                if (
                    matmul_states[i].threshold > 0.0
                    and not matmul_states[i].has_fp16_weights
                ):
                    matmul_states[i].use_pool = True

            new_x = bf_x.unsqueeze(0)

            out[:, current_index : current_index + output_size] = matmul(
                new_x, qweight[offsets[i] : offsets[i + 1]], state=matmul_states[i]
            )

            current_index += output_size

        out = out.to(original_type)

        if reshape_after_matmul:
            out = out.view(*original_shape[:-1], out.size(-1))

        if bias is not None:
            out += bias

        qweight.generation += 1

        return out