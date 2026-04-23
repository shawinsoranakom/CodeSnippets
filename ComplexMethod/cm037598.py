def process_weights_after_loading(self, layer: torch.nn.Module) -> None:
        num_experts = layer.w13_qweight.shape[0]
        device = layer.w13_qweight.device
        is_a_8bit = self.input_dtype is not None and self.input_dtype.itemsize == 1

        if self.input_dtype == torch.float8_e4m3fn:
            ops.marlin_int4_fp8_preprocess(
                layer.w13_qweight.view(-1, layer.w13_qweight.size(2)),
                layer.w13_qzeros.view(-1, layer.w13_qzeros.size(2)),
                inplace=True,
            )
            ops.marlin_int4_fp8_preprocess(
                layer.w2_qweight.view(-1, layer.w2_qweight.size(2)),
                layer.w2_qzeros.view(-1, layer.w2_qzeros.size(2)),
                inplace=True,
            )
            layer.w13_scales.data = layer.w13_scales.data * 512
            layer.w2_scales.data = layer.w2_scales.data * 512

        layer.w13_g_idx_sort_indices = torch.nn.Parameter(
            torch.empty((num_experts, 0), dtype=torch.int32, device=device),
            requires_grad=False,
        )
        layer.w2_g_idx_sort_indices = torch.nn.Parameter(
            torch.empty((num_experts, 0), dtype=torch.int32, device=device),
            requires_grad=False,
        )

        marlin_w13_qweight = ops.awq_marlin_moe_repack(
            layer.w13_qweight,
            layer.w13_g_idx_sort_indices,
            size_k=layer.w13_qweight.shape[1],
            size_n=layer.w13_qweight.shape[2] * self.quant_config.pack_factor,
            num_bits=self.quant_config.weight_bits,
            is_a_8bit=is_a_8bit,
        )
        replace_parameter(layer, "w13_qweight", marlin_w13_qweight)

        marlin_w2_qweight = ops.awq_marlin_moe_repack(
            layer.w2_qweight,
            layer.w2_g_idx_sort_indices,
            size_k=layer.w2_qweight.shape[1],
            size_n=layer.w2_qweight.shape[2] * self.quant_config.pack_factor,
            num_bits=self.quant_config.weight_bits,
            is_a_8bit=is_a_8bit,
        )
        replace_parameter(layer, "w2_qweight", marlin_w2_qweight)

        # The modular kernel expects w13_weight and w2_weight,
        # but AWQ uses w13_qweight and w2_qweight
        # Alias for modular kernel
        layer.w13_weight = layer.w13_qweight
        # Alias for modular kernel
        layer.w2_weight = layer.w2_qweight

        # Why does this take the intermediate size for size_k?
        marlin_w13_scales = marlin_moe_permute_scales(
            s=layer.w13_scales,
            size_k=layer.intermediate_size_per_partition,
            size_n=layer.w13_scales.shape[2],
            group_size=self.quant_config.group_size,
            is_a_8bit=is_a_8bit,
        )
        if self.input_dtype == torch.int8 and layer.num_groups_w13 > 1:
            marlin_w13_scales, w13_input_global_scale = marlin_act_int8_process_scales(
                marlin_w13_scales
            )
            layer.register_parameter(
                "w13_input_global_scale",
                Parameter(w13_input_global_scale, requires_grad=False),
            )

        replace_parameter(layer, "w13_scales", marlin_w13_scales)

        marlin_w2_scales = marlin_moe_permute_scales(
            s=layer.w2_scales,
            size_k=layer.intermediate_size_per_partition,
            size_n=layer.w2_scales.shape[2],
            group_size=self.quant_config.group_size,
            is_a_8bit=is_a_8bit,
        )
        if self.input_dtype == torch.int8 and layer.num_groups_w2 > 1:
            marlin_w2_scales, w2_input_global_scale = marlin_act_int8_process_scales(
                marlin_w2_scales
            )
            layer.register_parameter(
                "w2_input_global_scale",
                Parameter(w2_input_global_scale, requires_grad=False),
            )

        replace_parameter(layer, "w2_scales", marlin_w2_scales)

        marlin_w13_zp = moe_awq_to_marlin_zero_points(
            layer.w13_qzeros,
            size_k=layer.w13_qzeros.shape[1],
            size_n=layer.w13_qzeros.shape[2] * self.quant_config.pack_factor,
            num_bits=self.quant_config.weight_bits,
            is_a_8bit=is_a_8bit,
        )
        replace_parameter(layer, "w13_qzeros", marlin_w13_zp)

        marlin_w2_zp = moe_awq_to_marlin_zero_points(
            layer.w2_qzeros,
            size_k=layer.w2_qzeros.shape[1],
            size_n=layer.w2_qzeros.shape[2] * self.quant_config.pack_factor,
            num_bits=self.quant_config.weight_bits,
            is_a_8bit=is_a_8bit,
        )
        replace_parameter(layer, "w2_qzeros", marlin_w2_zp)

        if hasattr(layer, "w13_bias") and layer.w13_bias is not None:
            layer.w13_bias.data = marlin_permute_bias(layer.w13_bias)

        if hasattr(layer, "w2_bias") and layer.w2_bias is not None:
            layer.w2_bias.data = marlin_permute_bias(layer.w2_bias)