def process_weights_after_loading(self, layer: torch.nn.Module) -> None:
        # Discard zero points (INT8 fused MoE kernel uses symmetric quant)
        for attr in (
            "w13_input_zero_point",
            "w2_input_zero_point",
            "w13_weight_zero_point",
            "w2_weight_zero_point",
        ):
            if hasattr(layer, attr):
                delattr(layer, attr)

        # For static input scales, collapse per-expert scales to single max
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
                    "INT8 MoE layer. Using the maximum across experts "
                    "for each layer."
                )
            layer.w13_input_scale = torch.nn.Parameter(
                layer.w13_input_scale.max(), requires_grad=False
            )
            layer.w2_input_scale = torch.nn.Parameter(
                layer.w2_input_scale.max(), requires_grad=False
            )

        # For per-tensor weights, merge w1/w3 scales into single per-expert
        if self.weight_qscheme == "per_tensor":
            assert layer.w13_weight_scale is not None
            shard_size = layer.intermediate_size_per_partition
            max_w13_scales = layer.w13_weight_scale.max(dim=1).values

            for expert_id in range(layer.local_num_experts):
                start = 0
                for shard_id in range(2):
                    dq_weight = per_tensor_dequantize(
                        layer.w13_weight[expert_id][start : start + shard_size, :],
                        layer.w13_weight_scale[expert_id][shard_id],
                    )
                    layer.w13_weight[expert_id][start : start + shard_size, :], _, _ = (
                        ops.scaled_int8_quant(
                            dq_weight,
                            scale=max_w13_scales[expert_id],
                        )
                    )
                    start += shard_size

            layer.w13_weight_scale = torch.nn.Parameter(
                max_w13_scales, requires_grad=False
            )