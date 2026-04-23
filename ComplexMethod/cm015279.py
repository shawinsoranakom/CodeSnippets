def _test_qlinear_impl(self, batch_size, input_channels, output_channels, use_bias,
                           post_op, use_multi_dim_input, use_channelwise, **post_op_kwargs):
        decimal_val = 4
        dtypes = [torch.quint8]
        if torch.backends.quantized.engine == 'qnnpack':
            # QNNPACK supports uint8 in the kernels. In the op we shift the int8
            # weight values to uint8 to be on par with fbgemm. However, this causes
            # some rounding issues in rare cases. So, we relax the check to allow
            # off by one results.
            decimal_val = 0

            # only qnnpack qengine supports qint8 when xnnpack is available
            if torch.backends.xnnpack.enabled:
                dtypes.append(torch.qint8)

        if qengine_is_onednn() and IS_ARM64:
            dtypes.append(torch.qint8)

        for dtype in dtypes:
            # No support for channelwise in xnnpack (int8)
            if dtype == torch.qint8 and use_channelwise:
                return

            nptype = np_dtype[dtype]
            qlinear_prepack = torch.ops.quantized.linear_prepack
            if post_op == 'relu':
                qlinear = torch.ops.quantized.linear_relu
            elif post_op == 'leaky_relu':
                qlinear = torch.ops.quantized.linear_leaky_relu
            else:
                qlinear = torch.ops.quantized.linear
            if use_multi_dim_input:
                batch_size *= 3  # Test the multi-dim input tensor
            X_scale = 1.5
            X_zp = 5
            X_value_min = -128 if dtype == torch.qint8 else 0
            X_value_max = 127 if dtype == torch.qint8 else 255
            X_q0 = np.round(
                np.random.rand(batch_size, input_channels) *
                (X_value_max - X_value_min)
                + X_value_min
            ).astype(nptype)

            W_scales = np.random.rand(output_channels)
            # xnnpack forces W_zp to 0 when using symmetric quantization
            # ONEDNN only supports symmetric quantization of weight
            if dtype == torch.qint8 or qengine_is_onednn():
                W_zps = np.zeros(output_channels).astype(int)
            else:
                W_zps = np.round(np.random.rand(output_channels) * 100 - 50).astype(int)
            # when using symmetric quantization
            # special restriction for xnnpack fully connected op weight
            # [-127, 127] instead of [-128, 127]
            W_value_min = -127 if dtype == torch.qint8 else -128
            W_value_max = 127
            W_q0 = np.round(
                np.random.rand(output_channels, input_channels)
                * (W_value_max - W_value_min)
                + W_value_min
            ).astype(np.int8)  # weight is always int8_t
            b_value_min = -10
            b_value_max = 10
            b_q0 = np.round(
                np.random.rand(output_channels) *
                (b_value_max - b_value_min) + b_value_min
            ).astype(np.int32) if use_bias else None
            if torch.backends.quantized.engine in ('x86', 'fbgemm', 'onednn') and not IS_ARM64:
                avoid_vpmaddubsw_overflow_linear(
                    batch_size,
                    input_channels,
                    output_channels,
                    X_q0,
                    X_value_min,
                    X_value_max,
                    W_q0,
                    W_value_min,
                    W_value_max,
                )
            X = torch.from_numpy(_dequantize(
                X_q0, X_scale, X_zp)).to(dtype=torch.float)
            X_q = torch.quantize_per_tensor(
                X, scale=X_scale, zero_point=X_zp, dtype=dtype)
            if use_channelwise:
                W = torch.from_numpy(_dequantize(W_q0, W_scales.reshape(
                    (-1, 1)), W_zps.reshape((-1, 1)))).to(dtype=torch.float)
                W_q = torch.quantize_per_channel(W, scales=torch.from_numpy(W_scales),
                                                 zero_points=torch.from_numpy(W_zps), axis=0, dtype=torch.qint8)
                b = torch.from_numpy(_dequantize(
                    b_q0, X_scale * W_scales, 0)).to(dtype=torch.float) if use_bias else None
                b_q = torch.quantize_per_channel(b, scales=torch.from_numpy(X_scale * W_scales),
                                                 zero_points=torch.zeros(output_channels, dtype=torch.long),
                                                 axis=0, dtype=torch.qint32) if use_bias else None
            else:
                W = torch.from_numpy(_dequantize(
                    W_q0, W_scales[0], W_zps[0])).to(dtype=torch.float)
                W_q = torch.quantize_per_tensor(W, scale=W_scales[0], zero_point=(
                    W_zps[0].astype(int).item()), dtype=torch.qint8)
                b = torch.from_numpy(_dequantize(
                    b_q0, X_scale * (W_scales[0].item()), 0)).to(dtype=torch.float) if use_bias else None
                b_q = torch.quantize_per_tensor(
                    b, scale=X_scale * (W_scales[0].item()), zero_point=0, dtype=torch.qint32) if use_bias else None
            # Compare X_scale * W_scale * input_channels * X_value_max * W_value_max with
            # Y_scale * 255 (max for uint8).
            Y_scale = 12.34
            Y_zp = 5
            # Weight prepacking operator for quantized Linear
            float_bias = b if use_bias else None
            W_prepack = qlinear_prepack(W_q, float_bias)
            if use_multi_dim_input:
                X_q = X_q.view(3, int(batch_size / 3), input_channels)
            # Quantized Linear operator with prepacked weight
            Y_q = qlinear(X_q, W_prepack, Y_scale, Y_zp, **post_op_kwargs)
            if not use_channelwise and post_op in ('none', 'relu'):
                # Test the per-tensor quantization only
                # Reference quantized Linear operator
                Y_q_ref = qlinear_ref(X_q0, X_scale, X_zp, W_q0,
                                      W_scales[0], W_zps[0], b_q0, Y_scale, Y_zp, dtype=nptype)
                if post_op == 'relu':
                    Y_q_ref[Y_q_ref < Y_zp] = Y_zp
                if use_multi_dim_input:
                    Y_q_ref = np.reshape(
                        Y_q_ref, (3, int(batch_size / 3), output_channels))
                # Assert equal
                np.testing.assert_array_almost_equal(Y_q_ref, Y_q.int_repr().numpy(), decimal=decimal_val)
            # Test both per-tensor and per-channel quantization
            # Reference quantized result from PyTorch Linear operator
            W_fp32 = W_q.dequantize().to(dtype=torch.float)
            X_fp32 = X_q.dequantize().to(dtype=torch.float)
            b_fp32 = b_q.dequantize().to(dtype=torch.float) if use_bias else None
            Y_fp32_ref = F.linear(X_fp32, W_fp32, b_fp32)
            if post_op == 'relu':
                Y_fp32_ref[Y_fp32_ref < 0.0] = 0.0
            elif post_op == 'leaky_relu':
                Y_fp32_ref = F.leaky_relu(Y_fp32_ref, **post_op_kwargs)
            Y_q_ref2 = torch.quantize_per_tensor(
                Y_fp32_ref, Y_scale, Y_zp, dtype)
            # Assert equal
            np.testing.assert_array_almost_equal(
                Y_q_ref2.int_repr().numpy(), Y_q.int_repr().numpy(), decimal=decimal_val)