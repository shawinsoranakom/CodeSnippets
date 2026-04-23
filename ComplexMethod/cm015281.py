def test_qlinear_cudnn(self, batch_size, input_channels, output_channels, use_bias,
                           use_relu, use_multi_dim_input, use_channelwise):
        qlinear_prepack = torch.ops.quantized.linear_prepack
        if use_relu:
            qlinear_op = torch.ops.quantized.linear_relu
        else:
            qlinear_op = torch.ops.quantized.linear
        X_scale = 1.5
        X_zp = 0
        X_value_min = -128
        X_value_max = 127
        X_q0 = np.round(
            np.random.rand(batch_size, input_channels) *
            (X_value_max - X_value_min)
            + X_value_min).astype(np.int8)
        W_scale = 2.5
        W_zp = 0
        W_value_min = -128
        W_value_max = 127
        W_q0 = np.round(
            np.random.rand(output_channels, input_channels)
            * (W_value_max - W_value_min)
            + W_value_min
        ).astype(np.int8)
        b_value_min = -10
        b_value_max = 10
        b_q0 = np.round(
            np.random.rand(output_channels) *
            (b_value_max - b_value_min) + b_value_min
        ).astype(np.int32) if use_bias else None
        if use_bias:
            b_value_min = -10
            b_value_max = 10
            b_q0 = np.round(
                np.random.rand(output_channels) *
                (b_value_max - b_value_min) + b_value_min
            ).astype(np.int32)
        else:
            bias = None
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
        quant_dtype = torch.qint8
        X = torch.from_numpy(_dequantize(
            X_q0, X_scale, X_zp)).to(dtype=torch.float).to(device="cuda")
        X_q = torch.quantize_per_tensor(
            X, scale=X_scale, zero_point=X_zp, dtype=quant_dtype)
        W = torch.from_numpy(_dequantize(
            W_q0, W_scale, W_zp)).to(dtype=torch.float).to(device="cuda")
        W_q = torch.quantize_per_tensor(W, scale=W_scale, zero_point=W_zp, dtype=quant_dtype)
        b = torch.from_numpy(_dequantize(
            b_q0, X_scale * (W_zp), 0)).to(dtype=torch.float).to(device="cuda") if use_bias else None
        b_q = torch.quantize_per_tensor(
            b, scale=X_scale * W_scale, zero_point=0, dtype=quant_dtype) if use_bias else None
        Y_scale = 0.5
        Y_zp = 0
        # Weight prepacking operator for quantized Linear
        float_bias = b if use_bias else None
        W_prepack = qlinear_prepack(W_q, float_bias if use_bias else None)
        # Quantized Linear operator with prepacked weight
        Y_q = qlinear_op(X_q, W_prepack, Y_scale, Y_zp).to(device="cpu")
        Y_q_ref = qlinear_ref(X_q0, X_scale, X_zp, W_q0,
                              W_scale, W_zp, b_q0, Y_scale, Y_zp, dtype=np.int8)
        if use_relu:
            Y_q_ref[Y_q_ref < Y_zp] = Y_zp
        decimal_val = 0
        np.testing.assert_array_almost_equal(Y_q_ref, Y_q.int_repr().numpy(), decimal=decimal_val)