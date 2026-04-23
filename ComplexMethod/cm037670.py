def process_weights_after_loading(self, layer: torch.nn.Module) -> None:
        # Fp8 moe kernels require a single activation scale.
        # We take the max of all the scales in case they differ.
        if self.static_input_scales:
            if layer.w13_input_scale is None or layer.w2_input_scale is None:
                raise ValueError(
                    "QuantConfig has static quantization, but found "
                    "activation scales are None."
                )
            if not all_close_1d(layer.w13_input_scale) or not all_close_1d(
                layer.w2_input_scale
            ):
                logger.warning_once(
                    "Found input_scales that are not equal for "
                    "fp8 MoE layer. Using the maximum across experts "
                    "for each layer. "
                )
            layer.w13_input_scale = torch.nn.Parameter(
                layer.w13_input_scale.max(), requires_grad=False
            )
            layer.w2_input_scale = torch.nn.Parameter(
                layer.w2_input_scale.max(), requires_grad=False
            )

        if current_platform.is_fp8_fnuz():
            # Normalize the weights and scales
            w13_weight, w13_weight_scale, w13_input_scale = (
                normalize_e4m3fn_to_e4m3fnuz(
                    layer.w13_weight, layer.w13_weight_scale, layer.w13_input_scale
                )
            )
            w2_weight, w2_weight_scale, w2_input_scale = normalize_e4m3fn_to_e4m3fnuz(
                layer.w2_weight, layer.w2_weight_scale, layer.w2_input_scale
            )
            # Reset the parameter
            layer.w13_weight = torch.nn.Parameter(w13_weight, requires_grad=False)
            layer.w13_weight_scale = torch.nn.Parameter(
                w13_weight_scale, requires_grad=False
            )
            if w13_input_scale is not None:
                layer.w13_input_scale = torch.nn.Parameter(
                    w13_input_scale, requires_grad=False
                )
            layer.w2_weight = torch.nn.Parameter(w2_weight, requires_grad=False)
            layer.w2_weight_scale = torch.nn.Parameter(
                w2_weight_scale, requires_grad=False
            )
            if w2_input_scale is not None:
                layer.w2_input_scale = torch.nn.Parameter(
                    w2_input_scale, requires_grad=False
                )

        # For per-tensor case, Fp8 moe kernel needs single weight scale
        # for w13 per expert. Use max then dequant and requant each expert.
        if self.weight_qscheme == "per_tensor":
            assert layer.w13_weight_scale is not None
            shard_size = layer.intermediate_size_per_partition
            max_w13_scales = layer.w13_weight_scale.max(dim=1).values

            # For gpt_oss, w1 and w3 are fused into a single combined
            # gate_up_proj tensor with size 2*intermediate_size_per_partition
            # and only one scale per expert.
            # Process the entire weight tensor as one shard.
            if self.model_type == "gpt_oss":
                for expert_id in range(layer.local_num_experts):
                    # Process all 2*intermediate_size_per_partition rows at once
                    dq_weight = per_tensor_dequantize(
                        layer.w13_weight[expert_id],
                        layer.w13_weight_scale[expert_id][0],
                    )
                    layer.w13_weight[expert_id], _ = ops.scaled_fp8_quant(
                        dq_weight, max_w13_scales[expert_id]
                    )
            else:
                # For non-gpt_oss, process w1 and w3 shards separately
                for expert_id in range(layer.local_num_experts):
                    start = 0
                    for shard_id in range(2):
                        dq_weight = per_tensor_dequantize(
                            layer.w13_weight[expert_id][start : start + shard_size, :],
                            layer.w13_weight_scale[expert_id][shard_id],
                        )
                        (
                            layer.w13_weight[expert_id][start : start + shard_size, :],
                            _,
                        ) = ops.scaled_fp8_quant(dq_weight, max_w13_scales[expert_id])
                        start += shard_size

            layer.w13_weight_scale = torch.nn.Parameter(
                max_w13_scales, requires_grad=False
            )

        # quark's scale is 1 dim.
        elif self.weight_qscheme == "per_channel":
            if self.act_quant_group_shape == GroupShape.PER_TOKEN:
                w13_weight_scale = layer.w13_weight_scale.unsqueeze(-1)
                layer.w13_weight_scale = torch.nn.Parameter(
                    w13_weight_scale, requires_grad=False
                )
                w2_weight_scale = layer.w2_weight_scale.unsqueeze(-1)
                layer.w2_weight_scale = torch.nn.Parameter(
                    w2_weight_scale, requires_grad=False
                )
        # Property to determine if AITER is used
        if self.rocm_aiter_moe_enabled:
            # reshaping weights is required for aiter moe kernel.
            shuffled_w13, shuffled_w2 = rocm_aiter_ops.shuffle_weights(
                layer.w13_weight.data, layer.w2_weight.data
            )

            layer.w13_weight = torch.nn.Parameter(shuffled_w13, requires_grad=False)
            layer.w2_weight = torch.nn.Parameter(shuffled_w2, requires_grad=False)

        elif self.use_marlin:
            w13_weight, w2_weight, w13_weight_scale, w2_weight_scale = (
                prepare_fp8_moe_layer_for_marlin(
                    layer,
                    layer.w13_weight,
                    layer.w2_weight,
                    layer.w13_weight_scale,
                    layer.w2_weight_scale,
                )
            )
            # TODO(rob): once we apply refactor to Quark, switch to using
            # replace_parameter for compatibility with reloading in RL.
            layer.w13_weight = torch.nn.Parameter(w13_weight, requires_grad=False)
            layer.w2_weight = torch.nn.Parameter(w2_weight, requires_grad=False)
            layer.w13_weight_scale = torch.nn.Parameter(
                w13_weight_scale, requires_grad=False
            )
            layer.w2_weight_scale = torch.nn.Parameter(
                w2_weight_scale, requires_grad=False
            )