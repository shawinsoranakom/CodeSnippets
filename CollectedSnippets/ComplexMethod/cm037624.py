def _setup_kernel(
        self,
        layer: FusedMoE,
        w13: torch.Tensor,
        w2: torch.Tensor,
        w13_scale: torch.Tensor,
        w2_scale: torch.Tensor,
        w13_bias: torch.Tensor | None = None,
        w2_bias: torch.Tensor | None = None,
    ) -> None:
        num_experts = self.num_experts
        intermediate_size = self.intermediate_size
        hidden_size = self.hidden_size
        sf_block_size = 32

        # Shape assertions
        assert (
            w13.dim() == 3
            and w13.shape[0] == num_experts
            and w13.shape[1] == intermediate_size * 2
            and w13.shape[2] == hidden_size // 2
        )
        assert (
            w13_scale.dim() == 3
            and w13_scale.shape[0] == num_experts
            and w13_scale.shape[1] == intermediate_size * 2
            and w13_scale.shape[2] == hidden_size // sf_block_size
        )
        assert (
            w2.dim() == 3
            and w2.shape[0] == num_experts
            and w2.shape[1] == hidden_size
            and w2.shape[2] == intermediate_size // 2
        )
        assert (
            w2_scale.dim() == 3
            and w2_scale.shape[1] == hidden_size
            and w2_scale.shape[2] == intermediate_size // sf_block_size
        )
        if w13_bias is not None:
            assert (
                w13_bias.dim() == 2
                and w13_bias.shape[0] == num_experts
                and w13_bias.shape[1] == intermediate_size * 2
            )
        if w2_bias is not None:
            assert (
                w2_bias.dim() == 2
                and w2_bias.shape[0] == num_experts
                and w2_bias.shape[1] == hidden_size
            )

        # Convert weights to kernel format
        w13, w2, w13_scale, w2_scale, w13_bias, w2_bias = (
            convert_gpt_oss_weight_to_mxfp4_moe_kernel_format(
                mxfp4_backend=self.mxfp4_backend,
                layer=layer,
                w13_weight=w13,
                w2_weight=w2,
                w13_weight_scale=w13_scale,
                w2_weight_scale=w2_scale,
                w13_bias=w13_bias,
                w2_bias=w2_bias,
                _cache_permute_indices=self._cache_permute_indices,
            )
        )

        # For TRITON backends, weights are wrapped tensors from triton_kernels
        # that don't support .detach(). Manually assign parameters.
        if self.mxfp4_backend not in TRITON_BACKENDS:
            replace_parameter(layer, "w13_weight", w13)
            replace_parameter(layer, "w2_weight", w2)
            replace_parameter(layer, "w13_weight_scale", w13_scale)
            replace_parameter(layer, "w2_weight_scale", w2_scale)
        else:
            layer.w13_weight = w13
            layer.w2_weight = w2
            self.w13_precision_config = w13_scale
            self.w2_precision_config = w2_scale

        if w13_bias is not None and w2_bias is not None:
            replace_parameter(layer, "w13_bias", w13_bias)
            replace_parameter(layer, "w2_bias", w2_bias)

        # Build quant config
        self.moe_quant_config = self.get_fused_moe_quant_config(layer)

        # Build kernel (modular or monolithic)
        if self.moe_quant_config is not None and self.experts_cls is not None:
            self.moe_kernel = make_mxfp4_moe_kernel(
                moe_quant_config=self.moe_quant_config,
                moe_config=self.moe,
                mxfp4_backend=self.mxfp4_backend,
                experts_cls=self.experts_cls,
                routing_tables=layer._maybe_init_expert_routing_tables(),
                shared_experts=layer.shared_experts,
            )