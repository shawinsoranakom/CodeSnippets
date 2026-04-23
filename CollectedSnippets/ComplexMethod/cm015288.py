def test_qconv_transpose1d(self):
        if not qengine_is_qnnpack():
            return  # Currently only the QNNPACK is supported
        if qengine_is_qnnpack() and IS_PPC:
            return  # QNNPACK doesn't support these
        batch_size = 2
        input_channels_per_group_list = [2, 32]
        width = 14
        output_channels_per_group_list = [2, 8]
        groups_list = [1, 3]
        kernel_list = [1, 7]
        stride_list = [1, 2]
        pad = 2
        o_pad = 0
        dilation = 1
        X_scale = 1.2
        X_zero_point = 1
        W_scale = [1.2]
        W_zero_point = [1]
        Y_scale = 4.2
        Y_zero_point = 2
        use_bias_list = [True, False]

        test_cases = itertools.product(
            input_channels_per_group_list, output_channels_per_group_list,
            groups_list, kernel_list, stride_list, use_bias_list)
        for input_channels_per_group, output_channels_per_group, \
                groups, kernel, stride, use_bias in test_cases:

            input_channels = input_channels_per_group * groups
            output_channels = output_channels_per_group * groups
            kernels = (kernel,)
            strides = (stride,)
            pads = (pad,)
            o_pads = (o_pad,)
            dilations = (dilation,)

            qconv = torch.ops.quantized.conv_transpose1d
            qconv_prepack = torch.ops.quantized.conv_transpose1d_prepack
            conv_op = torch.nn.ConvTranspose1d(
                in_channels=input_channels,
                out_channels=output_channels,
                kernel_size=kernels,
                stride=strides,
                padding=pads,
                output_padding=o_pads,
                groups=groups,
                dilation=dilations,
                bias=use_bias
            )

            act_qdtypes = [torch.quint8]
            # Only qnnpack qengine supports qint8
            if qengine_is_qnnpack() and torch.backends.xnnpack.enabled:
                act_qdtypes.append(torch.qint8)

            for X_qdtype in act_qdtypes:
                if X_qdtype == torch.qint8:
                    W_zero_point = [0 for i in range(len(W_zero_point))]

                X_q, W_q, bias_float = self._test_qconv_impl(
                    qconv, qconv_prepack, conv_op, batch_size,
                    input_channels_per_group, (width, ),
                    output_channels_per_group, groups, kernels, strides, pads, o_pads,
                    dilations, X_scale, X_zero_point, W_scale, W_zero_point,
                    Y_scale, Y_zero_point, use_bias, post_op="none",
                    use_channelwise=False, use_transpose=True, input_dtype=X_qdtype, output_dtype=X_qdtype)

                # check that this doesn't error
                test_conv = torch.ao.nn.quantized.ConvTranspose1d(input_channels, output_channels, 1)
                test_conv.scale = Y_scale
                test_conv(X_q)

                # Test the module implementation
                qconv_op = torch.ao.nn.quantized.ConvTranspose1d(
                    in_channels=input_channels,
                    out_channels=output_channels,
                    kernel_size=kernels,
                    stride=strides,
                    padding=pads,
                    output_padding=o_pads,
                    groups=groups,
                    dilation=dilations,
                    bias=use_bias
                )
                qconv_op.scale = Y_scale
                qconv_op.zero_point = Y_zero_point
                qconv_op.set_weight_bias(W_q, bias_float)

                Y_dq_ref = conv_op(X_q.dequantize())
                Y_q_ref = torch.quantize_per_tensor(Y_dq_ref, scale=Y_scale,
                                                    zero_point=Y_zero_point,
                                                    dtype=X_qdtype)
                Y_q = qconv_op(X_q)
                self.assertEqual(Y_q_ref, Y_q)