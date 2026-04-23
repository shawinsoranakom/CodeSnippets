def _test_qlinear_fp8_helper(
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
        y_scale, y_zp = 0.3, 0
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
                    used_y_scale = 1.0
                    x2_scale, x2_zp = 1.0, 0
                else:
                    x2_scale, x2_zp = 0.3, 0
                x = torch.rand(batch_size, (ic + 1), ic) * 10 if input_dim == 3 else torch.rand(batch_size, ic) * 10
                w = torch.rand(oc, ic) * 10
                qx, x_scale = _quantize_fp8e4m3(x, channelwise=False)
                qw, w_scales = _quantize_fp8e4m3(w, channelwise=weight_quant_per_channel)
                if use_bias:
                    b = torch.rand(oc) * 10
                    if bfloat16_out:
                        b = b.to(torch.bfloat16)
                else:
                    b = None

                # compute reference result
                x_ref = _dequantize_fp8e4m3(qx, x_scale)
                w_ref = _dequantize_fp8e4m3(qw, w_scales)
                if b is not None:
                    y_ref = linear_op(x_ref, w_ref, b.to(torch.float))
                else:
                    y_ref = linear_op(x_ref, w_ref)

                # compute fp8 linear
                qw_packed = qlinear_prepack(qw, x.shape)
                x_zp = 0
                w_zps = torch.zeros_like(w_scales, dtype=torch.int)

                num_iter = 2 if test_fast_path else 1  # rerun to use cache
                if post_op in ("none", "relu", "gelu"):
                    for _ in range(num_iter):
                        qy = qlinear_op(
                            qx, x_scale, x_zp, qw_packed, w_scales, w_zps,
                            b, used_y_scale, used_y_zp, output_dtype,
                            post_op, unary_post_op_args, post_op_algo
                        )
                    if post_op == "relu":
                        y_ref = F.relu(y_ref)
                    elif post_op == "gelu":
                        y_ref = F.gelu(y_ref, approximate=post_op_algo)
                elif post_op in ("sum", "sum_relu"):
                    x2 = torch.rand_like(y_ref)
                    x2_q, x2_scale = _quantize_fp8e4m3(x2, channelwise=False)
                    x2_dq = _dequantize_fp8e4m3(x2_q, x2_scale)
                    unary_post_op = "relu" if post_op == "sum_relu" else "none"
                    binary_alpha = 1.0  # we only support alpha=1.0 now
                    # if output_dtype is fp32 or bf16, accumulate on x2
                    # if output_dtype is None (fp8), accumulate on x2_dq
                    accum = x2_q if output_dtype is None else x2
                    accum_ref = x2_dq if output_dtype is None else x2.clone()
                    x2_scale = x2_scale if output_dtype is None else 1.0
                    if bfloat16_out:
                        accum = accum.bfloat16()
                        accum_ref = accum_ref.bfloat16()
                    for _ in range(num_iter):
                        qy = qlinear_op(
                            qx, x_scale, x_zp, qw_packed, w_scales, w_zps,
                            accum.clone(), b, used_y_scale, used_y_zp, output_dtype,
                            x2_scale, x2_zp, "sum", binary_alpha,
                            unary_post_op, unary_post_op_args, post_op_algo
                        )
                    y_ref = y_ref + accum_ref * binary_alpha
                    if unary_post_op == "relu":
                        y_ref = F.relu(y_ref)
                elif post_op in ("add", "add_relu"):
                    if output_dtype is not None:
                        # Only support fp8 output
                        continue
                    x2 = torch.rand_like(y_ref)
                    unary_post_op = "relu" if post_op == "add_relu" else "none"
                    binary_alpha = 1.0  # we only support alpha=1.0 now
                    for _ in range(num_iter):
                        qy = qlinear_op(
                            qx, x_scale, x_zp, qw_packed, w_scales, w_zps,
                            x2, b, used_y_scale, used_y_zp, output_dtype,
                            1.0, 0, "add", binary_alpha,
                            unary_post_op, unary_post_op_args, post_op_algo
                        )
                    y_ref = y_ref + x2 * binary_alpha
                    if unary_post_op == "relu":
                        y_ref = F.relu(y_ref)

                # Compare results
                if output_dtype is None:
                    y_ref = _quantize_fp8e4m3(y_ref, False, used_y_scale)[0]
                else:
                    y_ref = y_ref.to(output_dtype)

                self.assertEqual(x.dim(), qy.dim())
                self.assertEqual(y_ref.float(), qy.float())
                if torch.isnan(qy).any():
                    raise AssertionError("Output qy contains NaN values")