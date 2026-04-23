def qconvolution_binary(
            x: TensorBox,
            x_scale,
            x_zp,
            packed_weight: TensorBox,
            w_scale: TensorBox,
            w_zp,
            accum: TensorBox,
            bias: TensorBox,
            stride,
            padding,
            dilation,
            groups,
            o_inv_scale,
            o_zero_point,
            output_dtype,
            accum_scale,
            accum_zp,
            binary_attr,
            alpha,
            unary_attr,
            unary_scalars,
            unary_algorithm,
        ):
            if not isinstance(x_scale, ir.TensorBox):
                assert type(x_scale) is float
                x_scale = V.graph.add_tensor_constant(
                    torch.tensor(x_scale, dtype=torch.float32), name="x_scale"
                )

            if x_zp is None:
                x_zp = V.graph.add_tensor_constant(
                    torch.tensor(0, dtype=torch.int32), name="x_zp"
                )
            if not isinstance(x_zp, ir.TensorBox):
                assert type(x_zp) is int
                x_zp = V.graph.add_tensor_constant(
                    torch.tensor(x_zp, dtype=torch.int32), name="x_zp"
                )

            if w_zp is None:
                w_zp = V.graph.add_tensor_constant(
                    torch.tensor(0, dtype=torch.int32), name="w_zp"
                )

            if (
                binary_attr == "sum"
                and output_dtype in [torch.float32, torch.bfloat16]
                and accum.get_dtype() in [torch.float32, torch.bfloat16]
                and accum.get_dtype() != output_dtype
            ):
                # For int8-mixed-bf16 quantization and inplace add,
                # there is case when accum dtype is float32 but output dtype is bfloat16.
                # Since the accum will be inplaced changed with post op sum,
                # we will do accum dtype conversion here.
                accum = to_dtype(accum, output_dtype)
            return TensorBox.create(
                mkldnn_ir.QConvPointWiseBinaryPT2E.create(
                    x,
                    x_scale,  # type: ignore[arg-type]
                    x_zp,  # type: ignore[arg-type]
                    packed_weight,
                    w_scale,
                    w_zp,
                    accum,
                    bias,
                    stride,
                    padding,
                    dilation,
                    groups,
                    o_inv_scale,
                    o_zero_point,
                    output_dtype,
                    accum_scale,
                    accum_zp,
                    binary_attr,
                    alpha,
                    unary_attr,
                    unary_scalars,
                    unary_algorithm,
                )
            )