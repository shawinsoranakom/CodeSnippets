def process_weights_after_loading(self, layer: FusedMoE) -> None:
        # Allow for accessing weights and scales in standard way.
        w13 = layer.w13_weight
        w2 = layer.w2_weight
        w13_scale = layer.w13_weight_scale
        w2_scale = layer.w2_weight_scale
        w13_input_scale = layer.w13_input_scale
        w2_input_scale = layer.w2_input_scale

        # MI300x and MI325x use FNUZ format for FP8. Convert if needed.
        if current_platform.is_fp8_fnuz():
            w13, w13_scale, w13_input_scale = normalize_e4m3fn_to_e4m3fnuz(
                w13, w13_scale, w13_input_scale
            )
            w2, w2_scale, w2_input_scale = normalize_e4m3fn_to_e4m3fnuz(
                w2, w2_scale, w2_input_scale
            )

        # Per tensor kernels require single activation scale. Use the max.
        if self.static_input_scales:
            assert self.input_quant.strategy == QuantizationStrategy.TENSOR
            assert w13_input_scale is not None and w2_input_scale is not None
            w13_input_scale, w2_input_scale = process_fp8_input_tensor_strategy_moe(
                w13_input_scale, w2_input_scale
            )
            replace_parameter(layer, "w13_input_scale", w13_input_scale)
            replace_parameter(layer, "w2_input_scale", w2_input_scale)

        # Per-tensor kernels use a single scale, for W13, but on disk there
        # is a separate scale for W1 and W3. Requantize with the max scale.
        if self.weight_quant.strategy == QuantizationStrategy.TENSOR:
            w13, w13_scale = process_fp8_weight_tensor_strategy_moe(
                w13,
                w13_scale,
                shard_size=layer.intermediate_size_per_partition,
                num_experts=layer.local_num_experts,
                is_act_and_mul=self.moe.is_act_and_mul,
            )

        w13, w2, w13_scale, w2_scale = convert_to_fp8_moe_kernel_format(
            fp8_backend=self.fp8_backend,
            layer=layer,
            w13=w13,
            w2=w2,
            w13_scale=w13_scale,
            w2_scale=w2_scale,
            w13_input_scale=w13_input_scale,
            w2_input_scale=w2_input_scale,
        )

        # Replace parameters with updated versions. Note that this helper
        # function ensures the replacement is compatible with RL weight reloads.
        replace_parameter(layer, "w13_weight", w13)
        replace_parameter(layer, "w2_weight", w2)
        replace_parameter(layer, "w13_weight_scale", w13_scale)
        replace_parameter(layer, "w2_weight_scale", w2_scale)

        # Setup modular kernel for TP case and naive DP/EP case.
        # In non-naive DP/EP case, we will create a ModularKernelMethod.
        # TODO(rob): unify these so FP8MoEMethod owns the ModularKernel
        # in both cases.
        self.moe_quant_config = self.get_fused_moe_quant_config(layer)
        if self.moe_quant_config:
            assert self.experts_cls is not None
            self.moe_kernel = make_fp8_moe_kernel(
                moe_quant_config=self.moe_quant_config,
                moe_config=self.moe,
                fp8_backend=self.fp8_backend,
                experts_cls=self.experts_cls,
                routing_tables=layer._maybe_init_expert_routing_tables(),
                shared_experts=layer.shared_experts,
            )