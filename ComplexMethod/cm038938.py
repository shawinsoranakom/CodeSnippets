def as_fused_moe_lora_expand_kwargs(
        self, ctx: BenchmarkContext, op_type: OpType
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

        # Expected input shape : [num_slices, num_tokens, top_k_num, lora_rank]
        assert len(i_shape) == 4
        assert i_shape[0] == num_slices
        assert i_shape[1] == num_tokens
        lora_rank = i_shape[-1]
        # Expected lora weight shape : [num_loras, num_experts, hidden_size, lora_rank]
        assert len(lw_shape) == 4
        assert lw_shape[-1] == lora_rank
        hidden_size = lw_shape[-2]
        # Expected output shape : [num_tokens, top_k_num, hidden_size * num_slices]
        assert len(o_shape) == 3
        assert o_shape == (num_tokens, ctx.top_k_num, hidden_size * num_slices)

        kernel_config = get_lora_op_configs(
            op_type.name.lower(),
            max_loras=lw_shape[0],
            batch=num_tokens,
            hidden_size=hidden_size,
            rank=lora_rank,
            num_slices=num_slices,
            add_inputs=False,
        )

        (topk_weights, sorted_token_ids, expert_ids, num_tokens_post_padded) = (
            self.fused_moe_lora_data_prepare(
                block_size=kernel_config["BLOCK_SIZE_M"],
                token_lora_mapping=self.lora_kernel_meta.token_lora_mapping,
                ctx=ctx,
            )
        )

        return {
            "a_intermediate_cache1": self.input,
            "lora_b_stacked": self.lora_weights_lst,
            "output": self.output,
            "topk_weights": topk_weights,
            "sorted_token_ids": sorted_token_ids,
            "expert_ids": expert_ids,
            "num_tokens_post_padded": num_tokens_post_padded,
            "token_lora_mapping": self.lora_kernel_meta.token_lora_mapping,
            "top_k_num": ctx.top_k_num,
            "device": self.input.device,
            "N": lora_rank,
            "M": topk_weights.shape[0],
            "EM": sorted_token_ids.shape[1],
            "K": self.input.shape[1],
            "num_tokens": num_tokens,
            "num_experts": ctx.num_experts,
            "num_slices": num_slices,
            "max_lora_rank": lora_rank,
            "w1_output_dim_size": lw_shape[2],
            "expand_block_size_m": kernel_config["BLOCK_SIZE_M"],
            "expand_block_size_n": kernel_config["BLOCK_SIZE_N"],
            "expand_block_size_k": kernel_config["BLOCK_SIZE_K"],
            "expand_group_size_m": kernel_config["GROUP_SIZE_M"],
            "expand_num_warps": kernel_config["NUM_WARPS"],
            "expand_num_stages": kernel_config["NUM_STAGES"],
            "expand_split_k": kernel_config.get("SPLIT_K", 1),
            "mul_routed_weight": op_type.is_fused_moe_lora_down_fn(),
        }