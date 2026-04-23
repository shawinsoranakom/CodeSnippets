def _test_qconv_impl_cpu_tensor_fp8(
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
        Y_scale=0.002,
        use_bias=True,
        post_op=PointwisePostOp(),
        use_channelwise=True,
        X2_scale=0.02,
        qconv_output_dtype=None,  # None, torch.float32, torch.bfloat16
        weight_in_channel_last_format=False,
    ):
        # We assume FP8 quantization is always symmetric
        fp32_output = qconv_output_dtype is torch.float32
        bfloat16_output = qconv_output_dtype is torch.bfloat16
        if fp32_output or bfloat16_output:
            Y_scale = 1.0
            X2_scale = 1.0
        batch_size = 3
        device = torch.device("cpu")
        use_transpose = False
        X, W, X_q, W_q, X_scale, W_scale, bias = self._make_qconv_tensors_fp8(
            batch_size,
            input_channels_per_group,
            input_feature_map_shape,
            output_channels_per_group,
            groups,
            kernels,
            strides,
            pads,
            dilations,
            use_bias,
            use_channelwise,
            use_transpose,
            bfloat16_output,
            device=device,
        )
        # Assign weights
        dqW = _dequantize_fp8e4m3(W_q, W_scale)
        dqX = _dequantize_fp8e4m3(X_q, X_scale)
        bias_float = bias.float() if use_bias and bfloat16_output else bias
        conv_op.weight = torch.nn.Parameter(dqW, requires_grad=False)
        conv_op.bias = (
            torch.nn.Parameter(bias_float, requires_grad=False) if use_bias else None
        )
        result_ref = conv_op(dqX)
        X2 = None
        X2_q = None
        X2_scale = 1.0

        if post_op.binary_attr == "sum":
            X2_dtype = qconv_output_dtype if qconv_output_dtype else torch.float32
            X2 = torch.rand_like(result_ref, device=device, dtype=X2_dtype)
            if qconv_output_dtype is None:
                X2_q, X2_scale = _quantize_fp8e4m3(X2, channelwise=False)
                X2_dq = _dequantize_fp8e4m3(X2_q, X2_scale)
                X2_scale = X2_scale.item()
            else:
                X2_dq = X2
            result_ref = result_ref + X2_dq
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
        if qconv_output_dtype is None:
            result_ref = _quantize_fp8e4m3(result_ref, False, Y_scale)[0]
        else:
            result_ref = result_ref.to(qconv_output_dtype)

        # Calculate the result for PT2E path
        if weight_in_channel_last_format:
            if W_q.dim() == 5:
                W_q = W_q.to(memory_format=torch.channels_last_3d)
            elif W_q.dim() == 4:
                W_q = W_q.to(memory_format=torch.channels_last)

        X_scale_scalar = X_scale.item()
        packed_weight = qconv_prepack(
            W_q,
            W_scale,
            X_scale_scalar,
            0,  # X_zero_point
            strides,
            pads,
            dilations,
            groups,
            X_q.size(),
        )

        if post_op.binary_attr == "sum":
            accum = (
                X2_q.contiguous(memory_format=torch.channels_last)
                if X2_q is not None
                else X2.contiguous(memory_format=torch.channels_last)
            )
            result = qconv(
                X_q,
                X_scale_scalar,
                0,  # X_zero_point
                packed_weight,
                W_scale,
                torch.zeros([], dtype=torch.int8),  # W_zero_point
                accum,
                bias,
                strides,
                pads,
                dilations,
                groups,
                Y_scale,
                0,  # Y_zero_point
                qconv_output_dtype,
                X2_scale,
                0,  # X2_zero_point
                post_op.binary_attr,
                post_op.alpha,
                post_op.unary_attr,
                post_op.scalars,
                post_op.algorithm,
            )
        else:
            result = qconv(
                X_q,
                X_scale_scalar,
                0,  # X_zero_point
                packed_weight,
                W_scale,
                torch.zeros([], dtype=torch.int8),  # W_zero_point
                bias,
                strides,
                pads,
                dilations,
                groups,
                Y_scale,
                0,  # Y_zero_point
                qconv_output_dtype,
                post_op.unary_attr,
                post_op.scalars,
                post_op.algorithm,
            )
        if fp32_output or bfloat16_output:
            self.assertTrue(result.dtype == qconv_output_dtype)

        self.assertEqual(result.float(), result_ref.float(), atol=1e-6, rtol=1e-5)
        if torch.isnan(result).any():
            raise AssertionError("Output result contains NaN values")