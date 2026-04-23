def test_qlinear(self, batch_size, input_channels, output_channels,
                     use_bias, use_relu, use_multi_dim_input, use_channelwise, reduce_range):
        if torch.backends.quantized.engine == 'qnnpack':
            reduce_range = False

        qlinear_prepack = torch.ops.quantized.linear_prepack
        if use_relu:
            qlinear_dynamic = torch.ops.quantized.linear_relu_dynamic
        else:
            qlinear_dynamic = torch.ops.quantized.linear_dynamic

        if use_multi_dim_input:
            batch_size *= 3  # Test the multi-dim input tensor

        X_scale = 1.0
        X_zp = 0
        X_value_min = 0
        X_value_max = 255
        if reduce_range:
            X_value_max = 127
        X_q0 = np.round(np.random.rand(batch_size, input_channels) *
                        (X_value_max - X_value_min) + X_value_min).astype(np.uint8)
        X_q0[0, 0] = X_value_min
        X_q0[0, 1] = X_value_max

        # W_scale = 1.0
        # W_zp = 0
        W_scales = np.ones(output_channels)
        W_zps = np.zeros(output_channels).astype(int)
        W_value_min = -128
        W_value_max = 127
        W_q0 = np.round(
            np.random.rand(output_channels, input_channels)
            * (W_value_max - W_value_min)
            + W_value_min
        ).astype(np.int8)
        W_q0[0, 0] = W_value_min
        W_q0[1, 0] = W_value_max

        b_value_min = -10
        b_value_max = 10
        b_q0 = np.round(
            np.random.rand(output_channels) *
            (b_value_max - b_value_min) + b_value_min
        ).astype(np.int32) if use_bias else None

        if torch.backends.quantized.engine in ('x86', 'fbgemm', 'onednn'):
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

        X_fp32 = torch.from_numpy(_dequantize(X_q0, X_scale, X_zp)).to(dtype=torch.float)
        if use_multi_dim_input:
            X_fp32 = X_fp32.view(3, int(batch_size / 3), input_channels)

        # W_scale, W_zp = _calculate_dynamic_qparams(W_fp32, torch.qint8)
        # We currently only check the case where W_scale = 1.0, W_zp = 0.

        if use_channelwise:
            W_fp32 = torch.from_numpy(_dequantize(W_q0, W_scales.reshape(
                (-1, 1)), W_zps.reshape((-1, 1)))).to(dtype=torch.float)
            W_q = torch.quantize_per_channel(W_fp32, scales=torch.from_numpy(W_scales),
                                             zero_points=torch.from_numpy(W_zps), axis=0, dtype=torch.qint8)
            b_fp32 = torch.from_numpy(
                _dequantize(b_q0, X_scale * W_scales, 0)
            ).to(dtype=torch.float) if use_bias else None
        else:
            W_fp32 = torch.from_numpy(_dequantize(
                W_q0, W_scales[0], W_zps[0])).to(dtype=torch.float)
            W_q = torch.quantize_per_tensor(W_fp32, scale=W_scales[0], zero_point=(
                W_zps[0].astype(int).item()), dtype=torch.qint8)
            b_fp32 = torch.from_numpy(
                _dequantize(b_q0, X_scale * int(W_scales[0].item()), 0)
            ).to(dtype=torch.float) if use_bias else None

        # Observe X_fp32 and determine X_scale and X_zero_point, this should match
        # internals of dynamic linear.
        X_scale, X_zp = _calculate_dynamic_qparams(X_fp32, torch.quint8, reduce_range)
        X_q = torch.quantize_per_tensor(X_fp32, scale=X_scale, zero_point=X_zp, dtype=torch.quint8)

        # Weight prepacking operator for dynamic quantized Linear
        W_prepack = qlinear_prepack(W_q, b_fp32)
        # Dynamic quantized Linear operator with prepacked weight
        Y_fp32 = qlinear_dynamic(X_q.dequantize(), W_prepack, reduce_range)
        # Y_fp32 = qlinear_dynamic(X_fp32, W_prepack, b_fp32)

        Y_fp32_ref = F.linear(X_q.dequantize(), W_q.dequantize(), b_fp32)
        # Y_fp32_ref = F.linear(X_fp32, W_fp32, b_fp32)
        # if use_multi_dim_input:
        #     Y_fp32_ref = Y_fp32_ref.view(3, int(batch_size / 3), output_channels)

        if use_relu:
            Y_fp32_ref[Y_fp32_ref < 0.0] = 0.0
        self.assertEqual(Y_fp32, Y_fp32_ref,
                         msg="torch.ops.quantized.linear_dynamic results are off")