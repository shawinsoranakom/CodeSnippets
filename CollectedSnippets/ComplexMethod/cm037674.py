def process_weights_after_loading(self, layer):
        from triton_kernels.matmul_ogs import FlexCtx, PrecisionConfig

        w13_bias = layer.w13_bias.to(torch.float32)
        w2_bias = layer.w2_bias.to(torch.float32)

        layer.w13_bias = torch.nn.Parameter(w13_bias, requires_grad=False)
        layer.w2_bias = torch.nn.Parameter(w2_bias, requires_grad=False)

        # FIXME warp need to be adjusted based on batch size
        # only apply to batched mode
        if self.moe.use_ep:
            num_warps = 4 if self.moe.max_num_tokens <= 512 else 8
        else:
            num_warps = 8

        w13_weight, w13_flex, w13_scale = _swizzle_mxfp4(
            layer.w13_weight, layer.w13_weight_scale, num_warps
        )
        w2_weight, w2_flex, w2_scale = _swizzle_mxfp4(
            layer.w2_weight, layer.w2_weight_scale, num_warps
        )

        self.w13_weight_triton_tensor = w13_weight
        self.w2_weight_triton_tensor = w2_weight

        # need to delete the original weights to save memory on single GPU
        del layer.w13_weight
        del layer.w2_weight
        layer.w13_weight = None
        layer.w2_weight = None
        torch.accelerator.empty_cache()

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
                    "for each layer."
                )

            layer.w13_input_scale = torch.nn.Parameter(
                layer.w13_input_scale.max().to(torch.float32), requires_grad=False
            )
            layer.w2_input_scale = torch.nn.Parameter(
                layer.w2_input_scale.max().to(torch.float32), requires_grad=False
            )

            from triton_kernels.numerics import InFlexData

            lhs_data13 = InFlexData(scale=layer.w13_input_scale)
            lhs_data2 = InFlexData(scale=layer.w2_input_scale)

            self.w13_precision_config = PrecisionConfig(
                weight_scale=w13_scale,
                flex_ctx=FlexCtx(rhs_data=w13_flex, lhs_data=lhs_data13),
            )

            self.w2_precision_config = PrecisionConfig(
                weight_scale=w2_scale,
                flex_ctx=FlexCtx(rhs_data=w2_flex, lhs_data=lhs_data2),
            )