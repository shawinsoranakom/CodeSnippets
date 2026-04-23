def _make_qconv_tensors(
        self, batch_size, input_channels_per_group, input_feature_map_shape,
        output_channels_per_group, groups, kernels, strides, pads, dilations,
        X_scale, X_zero_point, W_scale, W_zero_point,
        use_bias, use_channelwise, use_transpose,
        device=torch.device("cpu"),
        input_dtype=torch.quint8,
        weight_dtype=torch.qint8,
    ):
        if use_channelwise and use_transpose:
            raise AssertionError("Cannot generate channelwise qconv_transpose_tensors ")
        input_channels = input_channels_per_group * groups
        output_channels = output_channels_per_group * groups
        # Padded input size should be at least as big as dilated kernel
        kernels = _single(kernels)
        strides = _single(strides)
        pads = _single(pads)
        dilations = _single(dilations)
        for i in range(len(kernels)):
            assume(input_feature_map_shape[i] + 2 * pads[i]
                   >= dilations[i] * (kernels[i] - 1) + 1)
        W_scale = W_scale * output_channels
        W_zero_point = W_zero_point * output_channels
        # Resize W_scale and W_zero_points arrays equal to output_channels
        W_scale = W_scale[:output_channels]
        W_zero_point = W_zero_point[:output_channels]
        # For testing, we use small values for weights and for activations
        # so that no overflow occurs in vpmaddubsw instruction. If the
        # overflow occurs in qconv implementation and if there is no
        # overflow
        # In reference we can't exactly match the results with reference.
        # Please see the comment in qconv implementation file
        # aten/src/ATen/native/quantized/cpu/qconv.cpp for more details.
        (W_value_min, W_value_max) = (-5, 5)
        # the operator expects them in the format
        # (output_channels, input_channels/groups, kernel_d, kernel_h, kernel_w)
        # (input_channels, output_channels/groups, kernel_d, kernel_h, kernel_w)
        if use_transpose:
            output_shape = (input_channels, output_channels_per_group,)
        else:
            output_shape = (output_channels, input_channels_per_group,)
        W_init = torch.randint(
            W_value_min,
            W_value_max,
            output_shape + kernels,
            device=device,
        )
        b_init = torch.randint(0, 10, (output_channels,), device=device)

        (X_value_min, X_value_max) = (0, 4)
        X_init = torch.randint(
            X_value_min,
            X_value_max,
            (batch_size, input_channels,) + input_feature_map_shape,
            device=device
        )
        X = X_scale * (X_init - X_zero_point).float()

        if use_channelwise:
            W_shape = (-1, 1) + (1,) * len(kernels)
            W_scales_tensor = torch.tensor(W_scale, dtype=torch.float, device=device)
            W_zero_points_tensor = torch.tensor(W_zero_point, dtype=torch.float, device=device)
            W = W_scales_tensor.reshape(*W_shape) * (
                W_init.float() - W_zero_points_tensor.reshape(*W_shape)).float()
            b = X_scale * W_scales_tensor * b_init.float()
        else:
            W = W_scale[0] * (W_init - W_zero_point[0]).float()
            b = X_scale * W_scale[0] * b_init.float()

        X_q = torch.quantize_per_tensor(
            X, scale=X_scale, zero_point=X_zero_point, dtype=input_dtype)
        if use_channelwise:
            W_q = torch.quantize_per_channel(
                W, W_scales_tensor, W_zero_points_tensor.long(), 0,
                dtype=weight_dtype)
        else:
            W_q = torch.quantize_per_tensor(
                W, scale=W_scale[0], zero_point=W_zero_point[0],
                dtype=weight_dtype)

        bias_float = b if use_bias else None

        return (X, W), (X_q, W_q), bias_float