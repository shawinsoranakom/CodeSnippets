def process_weights_after_loading(self, layer: torch.nn.Module) -> None:
        is_a_8bit = self.input_dtype is not None and self.input_dtype.itemsize == 1

        if is_a_8bit:
            assert self.quant_type == scalar_types.uint4b8, (
                "W8A8-INT8 is not supported by marlin kernel."
            )

        if self.input_dtype == torch.float8_e4m3fn:
            ops.marlin_int4_fp8_preprocess(layer.w13_qweight, inplace=True)
            ops.marlin_int4_fp8_preprocess(layer.w2_qweight, inplace=True)
            layer.w13_scales.data = layer.w13_scales.data * 512
            layer.w2_scales.data = layer.w2_scales.data * 512

        # Process act_order
        if self.quant_config.desc_act:
            # Get sorting based on g_idx
            num_experts = layer.w13_g_idx.shape[0]
            w13_g_idx_sort_indices = torch.empty_like(layer.w13_g_idx)
            w2_g_idx_sort_indices = torch.empty_like(layer.w2_g_idx)
            w13_sorted_g_idx = torch.empty_like(layer.w13_g_idx)
            w2_sorted_g_idx = torch.empty_like(layer.w2_g_idx)
            for e in range(num_experts):
                w13_g_idx_sort_indices[e] = torch.argsort(layer.w13_g_idx[e]).to(
                    torch.int32
                )
                w2_g_idx_sort_indices[e] = torch.argsort(layer.w2_g_idx[e]).to(
                    torch.int32
                )
                w13_sorted_g_idx[e] = layer.w13_g_idx[e][w13_g_idx_sort_indices[e]]
                w2_sorted_g_idx[e] = layer.w2_g_idx[e][w2_g_idx_sort_indices[e]]
            replace_parameter(layer, "w13_g_idx", w13_sorted_g_idx)
            replace_parameter(layer, "w2_g_idx", w2_sorted_g_idx)
            replace_parameter(layer, "w13_g_idx_sort_indices", w13_g_idx_sort_indices)
            replace_parameter(layer, "w2_g_idx_sort_indices", w2_g_idx_sort_indices)
        else:
            # Reset g_idx related tensors
            num_experts = layer.w13_g_idx.shape[0]
            device = layer.w13_g_idx.device
            layer.w13_g_idx = torch.nn.Parameter(
                torch.empty((num_experts, 0), dtype=torch.int32, device=device),
                requires_grad=False,
            )
            layer.w2_g_idx = torch.nn.Parameter(
                torch.empty((num_experts, 0), dtype=torch.int32, device=device),
                requires_grad=False,
            )
            layer.w13_g_idx_sort_indices = torch.nn.Parameter(
                torch.empty((num_experts, 0), dtype=torch.int32, device=device),
                requires_grad=False,
            )
            layer.w2_g_idx_sort_indices = torch.nn.Parameter(
                torch.empty((num_experts, 0), dtype=torch.int32, device=device),
                requires_grad=False,
            )
        # Repack weights
        marlin_w13_qweight = ops.gptq_marlin_moe_repack(
            layer.w13_qweight,
            layer.w13_g_idx_sort_indices,
            layer.w13_qweight.shape[1] * self.quant_config.pack_factor,
            layer.w13_qweight.shape[2],
            self.quant_config.quant_type.size_bits,
            is_a_8bit=is_a_8bit,
        )
        replace_parameter(layer, "w13_qweight", marlin_w13_qweight)
        marlin_w2_qweight = ops.gptq_marlin_moe_repack(
            layer.w2_qweight,
            layer.w2_g_idx_sort_indices,
            layer.w2_qweight.shape[1] * self.quant_config.pack_factor,
            layer.w2_qweight.shape[2],
            self.quant_config.quant_type.size_bits,
            is_a_8bit=is_a_8bit,
        )
        replace_parameter(layer, "w2_qweight", marlin_w2_qweight)

        # The modular kernel expects w13_weight and w2_weight,
        # but GPTQ uses w13_qweight and w2_qweight
        # Alias for modular kernel
        layer.w13_weight = layer.w13_qweight
        # Alias for modular kernel
        layer.w2_weight = layer.w2_qweight

        # Repack scales
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
                torch.nn.Parameter(w13_input_global_scale, requires_grad=False),
            )

        replace_parameter(layer, "w13_scales", marlin_w13_scales)
        marlin_w2_scales = marlin_moe_permute_scales(
            s=layer.w2_scales,
            size_k=layer.w2_scales.shape[1]
            * (
                self.quant_config.group_size
                if self.quant_config.group_size != -1
                else self.quant_config.pack_factor
            ),
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
                torch.nn.Parameter(w2_input_global_scale, requires_grad=False),
            )

        replace_parameter(layer, "w2_scales", marlin_w2_scales)

        if hasattr(layer, "w13_bias") and layer.w13_bias is not None:
            layer.w13_bias.data = marlin_permute_bias(layer.w13_bias)

        if hasattr(layer, "w2_bias") and layer.w2_bias is not None:
            layer.w2_bias.data = marlin_permute_bias(layer.w2_bias)