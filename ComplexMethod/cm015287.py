def _test_qconv_impl(
        self, qconv_fn, qconv_prepack_fn, conv_op, batch_size,
        input_channels_per_group, input_feature_map_shape,
        output_channels_per_group, groups, kernels, strides, pads, o_pads,
        dilations, X_scale, X_zero_point, W_scale, W_zero_point, Y_scale,
        Y_zero_point, use_bias, post_op, use_channelwise, use_transpose,
        device=torch.device("cpu"),
        input_dtype=torch.quint8,
        weight_dtype=torch.qint8,
        output_dtype=torch.quint8,
        X2_scale=1.0,
        X2_zero_point=128
    ):
        # ONEDNN only supports symmetric quantization of weight
        if qengine_is_onednn() and W_zero_point is not None:
            W_zero_point = len(W_zero_point) * [0]
        (X, W), (X_q, W_q), bias_float = self._make_qconv_tensors(
            batch_size, input_channels_per_group, input_feature_map_shape,
            output_channels_per_group, groups, kernels,
            strides, pads, dilations, X_scale, X_zero_point, W_scale,
            W_zero_point, use_bias, use_channelwise, use_transpose,
            device=device, input_dtype=input_dtype, weight_dtype=weight_dtype)
        if bias_float is not None:
            bias_float = bias_float.to(device)
        # Assign weights
        W = W_q.dequantize()
        X = X_q.dequantize()
        conv_op.weight = torch.nn.Parameter(W, requires_grad=False)
        conv_op.bias = torch.nn.Parameter(
            bias_float, requires_grad=False) if use_bias else None
        result_ref = conv_op(X)
        if post_op == 'relu':
            if use_transpose:
                raise AssertionError("Cannot fuse ReLU with ConvTranspose")
            relu = torch.nn.ReLU()
            result_ref = relu(result_ref)
        elif post_op == 'add':
            (X_value_min, X_value_max) = (0, 4)
            X2_init = torch.randint(
                X_value_min,
                X_value_max,
                result_ref.size(),
                device=device
            )
            X2 = X2_scale * (X2_init - X2_zero_point).float()
            X2_q = torch.quantize_per_tensor(
                X2, scale=X2_scale, zero_point=X2_zero_point, dtype=input_dtype)
            result_ref = result_ref + X2
        elif post_op == 'add_relu':
            (X_value_min, X_value_max) = (0, 4)
            X2_init = torch.randint(
                X_value_min,
                X_value_max,
                result_ref.size(),
                device=device
            )
            X2 = X2_scale * (X2_init - X2_zero_point).float()
            X2_q = torch.quantize_per_tensor(
                X2, scale=X2_scale, zero_point=X2_zero_point, dtype=input_dtype)
            result_ref = result_ref + X2
            relu = torch.nn.ReLU()
            result_ref = relu(result_ref)
        # Quantize reference results for comparison
        result_ref_q = torch.quantize_per_tensor(
            result_ref, scale=Y_scale, zero_point=Y_zero_point,
            dtype=output_dtype)

        if qconv_prepack_fn is not None:
            if use_transpose:
                W_prepack = qconv_prepack_fn(
                    W_q, bias_float, strides, pads, o_pads, dilations, groups)
            else:
                W_prepack = qconv_prepack_fn(
                    W_q, bias_float, strides, pads, dilations, groups)
            if post_op == 'add' or post_op == 'add_relu':
                Y_q = qconv_fn(
                    X_q,
                    X2_q,
                    W_prepack,
                    Y_scale,
                    Y_zero_point,
                )
            else:
                Y_q = qconv_fn(
                    X_q,
                    W_prepack,
                    Y_scale,
                    Y_zero_point,
                )
        else:
            # quantized conv op without prepacking
            Y_q = qconv_fn(X_q, W_q, bias_float, strides, pads, dilations, groups, Y_scale, Y_zero_point)

        # Make sure the results match
        # assert_array_almost_equal compares using the following formula:
        #     abs(desired-actual) < 1.5 * 10**(-decimal)
        # (https://numpy.org/doc/stable/reference/generated/numpy.testing.assert_almost_equal.html)
        # We use decimal = 0 to ignore off-by-1 differences between
        # reference and test. Off-by-1 differences arise due to the order of
        # round and zero_point addition operation, i.e., if addition
        # followed by round is used by reference and round followed by
        # addition is used by test, the results may differ by 1.
        # For example, the result of round(2.5) + 1 is 3 while
        # round(2.5 + 1) is 4 assuming the rounding mode is
        # round-to-nearest, ties-to-even.
        np.testing.assert_array_almost_equal(
            result_ref_q.int_repr().cpu().numpy(), Y_q.int_repr().cpu().numpy(), decimal=0,
            err_msg=f'''X: {X_q}, W: {W_q}, b: {bias_float}, strides: {strides},
            pads: {pads}, o_pads: {o_pads}, dilations: {dilations},
            groups: {groups}, y_s: {Y_scale}, y_zp: {Y_zero_point}''')

        # Return the quantized data for later reuse
        return X_q, W_q, bias_float