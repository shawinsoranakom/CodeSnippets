def process_weights_after_loading(self, layer):
        if self.static_input_scales and self.input_dtype == "fp8":
            # firstly, process activations if fp8 static input
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
                _, _, w13_input_scale = normalize_e4m3fn_to_e4m3fnuz(
                    torch.empty_like(layer.w13_weight, dtype=torch.float8_e4m3fn),
                    torch.empty_like(
                        layer.w13_weight_scale, dtype=layer.w13_weight_scale.dtype
                    ),
                    layer.w13_input_scale,
                )
                _, _, w2_input_scale = normalize_e4m3fn_to_e4m3fnuz(
                    torch.empty_like(layer.w2_weight, dtype=torch.float8_e4m3fn),
                    torch.empty_like(
                        layer.w2_weight_scale, dtype=layer.w13_weight_scale.dtype
                    ),
                    layer.w2_input_scale,
                )
                # Reset the parameter
                if w13_input_scale is not None:
                    layer.w13_input_scale = torch.nn.Parameter(
                        w13_input_scale, requires_grad=False
                    )
                if w2_input_scale is not None:
                    layer.w2_input_scale = torch.nn.Parameter(
                        w2_input_scale, requires_grad=False
                    )

        # For w_mxfp4, use oracle functions
        if self.emulate or (
            self.ocp_mx_scheme == "w_mxfp4"
            and self.mxfp4_backend != Mxfp4MoeBackend.NONE
        ):
            self._setup_kernel_via_oracle(layer)
            return

        # TODO(bowenbao): gradually migrate to oracles.
        # Existing AITER path for w_mxfp4_a_mxfp4 and other schemes
        from aiter.utility.fp4_utils import e8m0_shuffle

        # Pre-shuffle weight scales
        s0, s1, _ = layer.w13_weight_scale.shape
        w13_weight_scale = layer.w13_weight_scale.view(s0 * s1, -1)
        w13_weight_scale = e8m0_shuffle(w13_weight_scale)
        layer.w13_weight_scale.data = w13_weight_scale.view(s0, s1, -1)

        s0, s1, _ = layer.w2_weight_scale.shape
        w2_weight_scale = layer.w2_weight_scale.view(s0 * s1, -1)
        w2_weight_scale = e8m0_shuffle(w2_weight_scale)
        layer.w2_weight_scale.data = w2_weight_scale.view(s0, s1, -1)

        if self.fp4_dtype is not None:
            layer.w13_weight = torch.nn.Parameter(
                layer.w13_weight.view(self.fp4_dtype),
                requires_grad=layer.w13_weight.requires_grad,
            )
            layer.w2_weight = torch.nn.Parameter(
                layer.w2_weight.view(self.fp4_dtype),
                requires_grad=layer.w2_weight.requires_grad,
            )
        # Pre-shuffle weight
        shuffled_w13, shuffled_w2 = rocm_aiter_ops.shuffle_weights(
            layer.w13_weight.data, layer.w2_weight.data
        )

        layer.w13_weight = torch.nn.Parameter(shuffled_w13, requires_grad=False)
        layer.w2_weight = torch.nn.Parameter(shuffled_w2, requires_grad=False)
        layer.w13_weight.is_shuffled = True
        layer.w2_weight.is_shuffled = True

        # Build quant config for AITER path
        self.moe_quant_config = self.get_fused_moe_quant_config(layer)
        torch.accelerator.empty_cache()