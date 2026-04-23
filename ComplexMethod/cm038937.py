def as_lora_expand_kwargs(
        self, ctx: BenchmarkContext, op_type: OpType, add_inputs: bool
    ) -> dict[str, Any]:
        self.sanity_check(ctx, op_type)
        self.to_device(self.input.device)

        _, num_tokens, _, num_slices = self.metadata(ctx, op_type)

        # Sanity check matrix shapes.
        i_shape, lw_shape, o_shape = (
            self.input.shape,
            self.lora_weights_lst[0].shape,
            self.output.shape,
        )
        # Expected input shape : [num_slices, num_tokens, lora_rank]
        assert len(i_shape) == 3
        assert i_shape[0] == num_slices
        assert i_shape[1] == num_tokens
        lora_rank = i_shape[2]
        # Expected lora weight shape : [num_lora, hidden_size, lora_rank]
        assert len(lw_shape) == 3
        assert lw_shape[2] == lora_rank
        hidden_size = lw_shape[1]
        # Expected output shape : [num_tokens, hidden_size * num_slices]
        assert len(o_shape) == 2
        assert o_shape == (num_tokens, hidden_size * num_slices)

        return {
            "inputs": self.input,
            "lora_b_weights": self.lora_weights_lst,
            "output_tensor": self.output,
            "token_lora_mapping": self.lora_kernel_meta.token_lora_mapping,
            "token_indices_sorted_by_lora_ids": (
                self.lora_kernel_meta.token_indices_sorted_by_lora_ids
            ),
            "num_tokens_per_lora": self.lora_kernel_meta.num_tokens_per_lora,
            "lora_token_start_loc": self.lora_kernel_meta.lora_token_start_loc,
            "lora_ids": self.lora_kernel_meta.active_lora_ids,
            "offset_start": 0,
            "add_inputs": add_inputs,
            "no_lora_flag_cpu": self.lora_kernel_meta.no_lora_flag_cpu,
        }