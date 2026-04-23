def process_weights_after_loading(self, layer: torch.nn.Module) -> None:
        E = layer.w13_weight.shape[0]
        H = layer.w13_in_features
        I2 = layer.w13_out_features
        IN = layer.w2_in_features
        g = layer.group_size

        def _pack_matrix(
            int4_as_int8_2d: torch.Tensor,
            scales_2d: torch.Tensor,
            bias_1d: torch.Tensor | None,
            in_features: int,
            out_features: int,
        ) -> torch.Tensor:
            # int4 values are stored as int8 in [-8,7].
            # Shift to unsigned nibble and pack pairs along input-dim.
            tmp = int4_as_int8_2d.add(8)  # [out, in]
            uint8_nibbles = ((tmp[:, 1::2] << 4) | tmp[:, ::2]).to(
                torch.uint8
            )  # [out, in//2]

            # KleidiAI groupwise kernels accepts float32 scales
            # KleidiAI groupwise kernels accepts bfloat16 scales
            scale_dtype = torch.float32 if g == -1 else torch.bfloat16
            scales = scales_2d.to(scale_dtype)
            bias = None if bias_1d is None else bias_1d.to(torch.float32)
            return torch.ops.aten._dyn_quant_pack_4bit_weight(
                uint8_nibbles,
                scales,
                bias,
                g if g != -1 else in_features,
                in_features,
                out_features,
            )

        # Pack per expert
        w13_packed_list = []
        w2_packed_list = []

        has_w13_bias = hasattr(layer, "w13_bias") and layer.w13_bias is not None
        has_w2_bias = hasattr(layer, "w2_bias") and layer.w2_bias is not None

        for e in range(E):
            w13_packed_list.append(
                _pack_matrix(
                    layer.w13_weight[e],  # [2I, H]
                    layer.w13_weight_scale[e],  # [2I, H/g or 1]
                    layer.w13_bias[e] if has_w13_bias else None,  # [2I]
                    H,
                    I2,
                )
            )
            w2_packed_list.append(
                _pack_matrix(
                    # w2 shape is [H, IN]; we need [out, in] == [H, IN].
                    layer.w2_weight[e],  # [H, IN]
                    layer.w2_weight_scale[e],  # [H, IN/g or 1]
                    layer.w2_bias[e] if has_w2_bias else None,  # [H]
                    IN,
                    layer.w2_out_features,  # in_features=IN, out_features=H
                )
            )

        # each packed tensor has identical shape per expert; stack on dim 0
        w13_packed = torch.stack(w13_packed_list, dim=0)
        w2_packed = torch.stack(w2_packed_list, dim=0)

        replace_parameter(
            layer,
            "w13_weight_packed",
            torch.nn.Parameter(w13_packed, requires_grad=False),
        )
        replace_parameter(
            layer,
            "w2_weight_packed",
            torch.nn.Parameter(w2_packed, requires_grad=False),
        )

        # free raw tensors/scales/bias now that they're packed into the payload.
        replace_parameter(
            layer, "w13_weight", torch.nn.Parameter(torch.empty(0), requires_grad=False)
        )
        replace_parameter(
            layer, "w2_weight", torch.nn.Parameter(torch.empty(0), requires_grad=False)
        )
        replace_parameter(
            layer,
            "w13_weight_scale",
            torch.nn.Parameter(torch.empty(0), requires_grad=False),
        )
        replace_parameter(
            layer,
            "w2_weight_scale",
            torch.nn.Parameter(torch.empty(0), requires_grad=False),
        )
        if has_w13_bias:
            replace_parameter(
                layer,
                "w13_bias",
                torch.nn.Parameter(torch.empty(0), requires_grad=False),
            )
        if has_w2_bias:
            replace_parameter(
                layer,
                "w2_bias",
                torch.nn.Parameter(torch.empty(0), requires_grad=False),
            )