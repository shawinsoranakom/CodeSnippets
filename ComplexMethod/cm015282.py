def _test_qlinear_pt2e_helper(
        self,
        qlinear_op,
        post_op="none",
        unary_post_op_args=(),
        post_op_algorithms=("none",),
    ):
        import os
        test_fast_path = os.getenv("ONEDNN_CACHE_CONTEXT_UNSAFE", "0") == "1"
        qlinear_prepack = torch.ops.onednn.qlinear_prepack
        linear_op = F.linear
        in_channels_list = [4, 8]
        out_channels_list = [16, 32]
        batch_size = 1
        use_bias_list = [True, False]
        weight_quant_per_channel_list = [True, False]
        output_dtype_list = [None, torch.float32, torch.bfloat16]
        x_scale, x_zp = 1.2, 1
        w_scale, w_zp = 0.8, 0
        y_scale, y_zp = 4.7, 2
        input_dim_list = [2, 3]
        cases = itertools.product(
            in_channels_list, out_channels_list, use_bias_list,
            weight_quant_per_channel_list, output_dtype_list, post_op_algorithms, input_dim_list)
        with override_quantized_engine('onednn'):
            for ic, oc, use_bias, weight_quant_per_channel, output_dtype, post_op_algo, input_dim in cases:
                used_y_scale = y_scale
                used_y_zp = y_zp
                fp32_out = output_dtype == torch.float32
                bfloat16_out = output_dtype == torch.bfloat16
                if fp32_out or bfloat16_out:
                    used_y_scale, used_y_zp = 1.0, 0
                    x2_scale, x2_zp = 1.0, 0
                else:
                    x2_scale, x2_zp = 2.3, 5
                x = torch.rand(batch_size, (ic + 1), ic) * 10 if input_dim == 3 else torch.rand(batch_size, ic) * 10
                w = torch.rand(oc, ic) * 10
                qx = torch.quantize_per_tensor(x, x_scale, x_zp, torch.quint8)
                if weight_quant_per_channel:
                    w_scales = torch.Tensor([w_scale] * oc)
                    w_zps = torch.zeros(oc).to(dtype=torch.int)
                    qw = torch.quantize_per_channel(w, w_scales, w_zps, 0, torch.qint8)
                else:
                    w_scales = torch.Tensor([w_scale])
                    w_zps = torch.Tensor([w_zp]).to(dtype=torch.int)
                    qw = torch.quantize_per_tensor(w, w_scale, w_zp, torch.qint8)
                if use_bias:
                    b = torch.rand(oc) * 10
                else:
                    b = None

                x_ref = qx.dequantize()
                w_ref = qw.dequantize()
                y_ref = linear_op(x_ref, w_ref, b)

                # compute with CPU tensors
                qx_cpu = qx.int_repr()
                qw_cpu = qw.int_repr()
                qw_packed = qlinear_prepack(qw_cpu, x.shape)

                num_iter = 2 if test_fast_path else 1  # rerun to use cache
                if post_op in ("none", "relu", "gelu"):
                    for _ in range(num_iter):
                        qy_cpu = qlinear_op(
                            qx_cpu, x_scale, x_zp, qw_packed, w_scales, w_zps,
                            b, used_y_scale, used_y_zp, output_dtype,
                            post_op, unary_post_op_args, post_op_algo
                        )
                    if post_op == "relu":
                        y_ref = F.relu(y_ref)
                    elif post_op == "gelu":
                        y_ref = F.gelu(y_ref, approximate=post_op_algo)
                    qy_ref = torch.quantize_per_tensor(y_ref, used_y_scale, used_y_zp, torch.quint8)
                elif post_op in ("sum", "sum_relu"):
                    x2_int8 = torch.randint(0, 4, y_ref.size())
                    x2 = x2_scale * ((x2_int8 - x2_zp).float())
                    qx2 = torch.quantize_per_tensor(
                        x2, scale=x2_scale, zero_point=x2_zp, dtype=torch.quint8
                    )
                    unary_post_op = "relu" if post_op == "sum_relu" else "none"
                    binary_alpha = 1.0  # we only support alpha=1.0 now
                    accum = qx2.int_repr() if output_dtype is None else qx2.dequantize()
                    if bfloat16_out:
                        accum = accum.bfloat16()
                    for _ in range(num_iter):
                        # clone accum otherwise it gets accumulated multiple times
                        qy_cpu = qlinear_op(
                            qx_cpu, x_scale, x_zp, qw_packed, w_scales, w_zps,
                            accum.clone(), b, used_y_scale, used_y_zp, output_dtype,
                            x2_scale, x2_zp, "sum", binary_alpha,
                            unary_post_op, unary_post_op_args, post_op_algo
                        )
                    y_ref = y_ref + x2 * binary_alpha
                    if unary_post_op == "relu":
                        y_ref = F.relu(y_ref)
                    qy_ref = torch.quantize_per_tensor(y_ref, used_y_scale, used_y_zp, torch.quint8)
                elif post_op in ("add", "add_relu"):
                    used_y_scale, used_y_zp = 1.0, 0
                    if output_dtype is not None:
                        # Only support int8 output
                        continue
                    x2 = torch.randn(y_ref.size()) * 10
                    unary_post_op = "relu" if post_op == "add_relu" else "none"
                    binary_alpha = 1.0  # we only support alpha=1.0 now
                    for _ in range(num_iter):
                        qy_cpu = qlinear_op(
                            qx_cpu, x_scale, x_zp, qw_packed, w_scales, w_zps,
                            x2, b, used_y_scale, used_y_zp, output_dtype,
                            1.0, 0, "add", binary_alpha,
                            unary_post_op, unary_post_op_args, post_op_algo
                        )
                    y_ref = y_ref + x2 * binary_alpha
                    if unary_post_op == "relu":
                        y_ref = F.relu(y_ref)
                    qy_ref = torch.quantize_per_tensor(y_ref, used_y_scale, used_y_zp, torch.quint8)

                # Compare results
                if fp32_out or bfloat16_out:
                    qy_cpu = torch.quantize_per_tensor(
                        qy_cpu.to(torch.float32),
                        used_y_scale,
                        used_y_zp, dtype=torch.quint8
                    ).int_repr()

                self.assertEqual(x.dim(), qy_cpu.dim())

                np.testing.assert_array_almost_equal(
                    qy_ref.int_repr().cpu().numpy(),
                    qy_cpu.cpu().numpy(),
                    decimal=0,
                    err_msg=f"""X: {x}, W: {w}, b: {b},
                    x_s: {x_scale}, x_zp: {x_zp},
                    w_s: {w_scale}, w_zp: {w_zp},
                    y_s: {y_scale}, y_zp: {y_zp}""",
                )