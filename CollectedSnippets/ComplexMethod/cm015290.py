def _test_qconv_impl_cpu_tensor(
        self,
        qconv,
        qconv_prepack,
        conv_op,
        input_channels_per_group=2,
        input_feature_map_shape=(),
        output_channels_per_group=2,
        groups=1,
        kernels=3,
        strides=(),
        pads=(),
        dilations=(),
        X_scale=1.3,
        X_zero_point=2,
        W_scale=(1.0,),
        W_zero_point=(0,),
        Y_scale=3.2,
        Y_zero_point=0,
        use_bias=True,
        post_op=PointwisePostOp(),
        use_channelwise=True,
        X2_scale=1.2,
        X2_zero_point=0,
        qconv_output_dtype=None,  # None, torch.float32, torch.bfloat16
        weight_in_channel_last_format=False,
        qconv_x2_dtype=None,
    ):
        # ONEDNN only supports symmetric quantization of weight
        if W_zero_point is not None:
            W_zero_point = len(W_zero_point) * [0]
        fp32_output = qconv_output_dtype is torch.float32
        bfloat16_output = qconv_output_dtype is torch.bfloat16
        if fp32_output or bfloat16_output:
            Y_scale = 1.0
            Y_zero_point = 0
            X2_scale = 1.0
            X2_zero_point = 0
        batch_size = 3
        o_pads = None
        device = torch.device("cpu")
        input_dtype = torch.quint8
        weight_dtype = torch.qint8
        output_dtype = torch.quint8
        use_transpose = False
        (X, W), (X_q, W_q), bias_float = self._make_qconv_tensors(
            batch_size,
            input_channels_per_group,
            input_feature_map_shape,
            output_channels_per_group,
            groups,
            kernels,
            strides,
            pads,
            dilations,
            X_scale,
            X_zero_point,
            W_scale,
            W_zero_point,
            use_bias,
            use_channelwise,
            use_transpose,
            device=device,
            input_dtype=input_dtype,
            weight_dtype=weight_dtype,
        )
        if bias_float is not None:
            bias_float = bias_float.to(device)
        # Assign weights
        W = W_q.dequantize()
        X = X_q.dequantize()
        conv_op.weight = torch.nn.Parameter(W, requires_grad=False)
        conv_op.bias = (
            torch.nn.Parameter(bias_float, requires_grad=False) if use_bias else None
        )
        result_ref = conv_op(X)
        X2_q = None

        if post_op.binary_attr == "sum":
            (X_value_min, X_value_max) = (0, 4)
            X2_init = torch.randint(
                X_value_min, X_value_max, result_ref.size(), device=device
            )
            X2 = X2_scale * ((X2_init - X2_zero_point).float())
            X2_q = torch.quantize_per_tensor(
                X2, scale=X2_scale, zero_point=X2_zero_point, dtype=input_dtype
            )
            result_ref = result_ref + X2
            if post_op.unary_attr == "relu":
                relu = torch.nn.ReLU()
                result_ref = relu(result_ref)
        elif post_op.unary_attr == "relu":
            if use_transpose:
                raise AssertionError("Cannot fuse ReLU with ConvTranspose")
            relu = torch.nn.ReLU()
            result_ref = relu(result_ref)
        elif post_op.unary_attr == "hardtanh":
            if use_transpose:
                raise AssertionError("Cannot fuse hardtanh with ConvTranspose")
            if len(post_op.scalars) != 2:
                raise AssertionError("For post op hardtanh, expect 2 parameters passed in")
            hardtanh = torch.nn.Hardtanh(min_val=post_op.scalars[0], max_val=post_op.scalars[1])
            result_ref = hardtanh(result_ref)
        elif post_op.unary_attr == "hardswish":
            if use_transpose:
                raise AssertionError("Cannot fuse hardswish with ConvTranspose")
            hardswish = torch.nn.Hardswish()
            result_ref = hardswish(result_ref)
        elif post_op.unary_attr == "swish":
            if use_transpose:
                raise AssertionError("Cannot fuse silu with ConvTranspose")
            silu = torch.nn.SiLU()
            result_ref = silu(result_ref)

        # Quantize reference results for comparison
        result_ref_q = torch.quantize_per_tensor(
            result_ref, scale=Y_scale, zero_point=Y_zero_point, dtype=output_dtype
        )

        # Calculate the result for 2.X path
        X_q_cpu_tensor = X_q.int_repr()
        W_q_cpu_tensor = W_q.int_repr()

        weight_scale = (
            W_q.q_per_channel_scales()
            if use_channelwise
            else torch.tensor(W_q.q_scale(), dtype=torch.double, device=device)
        )
        weight_zero_point = (
            W_q.q_per_channel_zero_points()
            if use_channelwise
            else torch.tensor(W_q.q_zero_point(), dtype=torch.int64, device=device)
        )

        if weight_in_channel_last_format:
            if W_q_cpu_tensor.dim() == 5:
                W_q_cpu_tensor = W_q_cpu_tensor.to(memory_format=torch.channels_last_3d)
            elif W_q_cpu_tensor.dim() == 4:
                W_q_cpu_tensor = W_q_cpu_tensor.to(memory_format=torch.channels_last)

        packed_weight = qconv_prepack(
            W_q_cpu_tensor,
            weight_scale,
            X_scale,
            X_zero_point,
            strides,
            pads,
            dilations,
            groups,
            X_q_cpu_tensor.size(),
        )

        if post_op.binary_attr == "sum":
            X2_cpu_tensor = (
                X2_q.int_repr()
                if qconv_output_dtype is None
                else X2_q.dequantize().to(qconv_x2_dtype)
            ).contiguous(memory_format=torch.channels_last)
            Y_q_cpu_tensor = qconv(
                X_q_cpu_tensor,
                X_scale,
                X_zero_point,
                packed_weight,
                weight_scale,
                weight_zero_point,
                X2_cpu_tensor,
                bias_float,
                strides,
                pads,
                dilations,
                groups,
                Y_scale,
                Y_zero_point,
                qconv_output_dtype,
                X2_scale,
                X2_zero_point,
                post_op.binary_attr,
                post_op.alpha,
                post_op.unary_attr,
                post_op.scalars,
                post_op.algorithm,
            )
        else:
            Y_q_cpu_tensor = qconv(
                X_q_cpu_tensor,
                X_scale,
                X_zero_point,
                packed_weight,
                weight_scale,
                weight_zero_point,
                bias_float,
                strides,
                pads,
                dilations,
                groups,
                Y_scale,
                Y_zero_point,
                qconv_output_dtype,
                post_op.unary_attr,
                post_op.scalars,
                post_op.algorithm,
            )
        if fp32_output or bfloat16_output:
            self.assertTrue(Y_q_cpu_tensor.dtype == qconv_output_dtype)
            Y_q_cpu_tensor = torch.quantize_per_tensor(
                Y_q_cpu_tensor
                if fp32_output
                else Y_q_cpu_tensor.to(torch.float32), scale=Y_scale, zero_point=Y_zero_point, dtype=output_dtype
            ).int_repr()

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
            result_ref_q.int_repr().cpu().numpy(),
            Y_q_cpu_tensor.cpu().numpy(),
            decimal=0,
            err_msg=f"""X: {X_q}, W: {W_q}, b: {bias_float}, strides: {strides},
            pads: {pads}, o_pads: {o_pads}, dilations: {dilations},
            groups: {groups}, y_s: {Y_scale}, y_zp: {Y_zero_point}, X2: {X2_q}""",
        )

        # Return the quantized data for later reuse
        return X_q, W_q, bias_float