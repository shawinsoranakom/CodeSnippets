def test_qconv_transpose2d(
            self,
            batch_size,
            input_channels_per_group,
            height,
            width,
            output_channels_per_group,
            groups,
            kernel_h,
            kernel_w,
            stride_h,
            stride_w,
            pad_h,
            pad_w,
            o_pad_h,
            o_pad_w,
            dilation,
            X_scale,
            X_zero_point,
            W_scale,
            W_zero_point,
            Y_scale,
            Y_zero_point,
            use_bias):
        if qengine_is_qnnpack() and IS_PPC:
            return  # QNNPACK doesn't support these
        # ONEDNN does not support output paddings
        if qengine_is_onednn() and (o_pad_h, o_pad_w) != (0, 0):
            return
        assume(o_pad_h < stride_h and o_pad_h < dilation)
        assume(o_pad_w < stride_w and o_pad_w < dilation)

        input_channels = input_channels_per_group * groups
        output_channels = output_channels_per_group * groups
        kernels = (kernel_h, kernel_w)
        strides = (stride_h, stride_w)
        pads = (pad_h, pad_w)
        o_pads = (o_pad_h, o_pad_w)
        dilations = (dilation, dilation)

        qconv = torch.ops.quantized.conv_transpose2d
        qconv_prepack = torch.ops.quantized.conv_transpose2d_prepack
        conv_op = torch.nn.ConvTranspose2d(
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
                input_channels_per_group, (height, width),
                output_channels_per_group, groups, kernels, strides, pads, o_pads,
                dilations, X_scale, X_zero_point, W_scale, W_zero_point,
                Y_scale, Y_zero_point, use_bias, post_op="none",
                use_channelwise=False, use_transpose=True, input_dtype=X_qdtype, output_dtype=X_qdtype)

            # check that this doesn't error
            test_conv = torch.ao.nn.quantized.ConvTranspose2d(input_channels, output_channels, 1)
            test_conv.scale = Y_scale
            test_conv(X_q)

            # Test the module implementation
            qconv_op = torch.ao.nn.quantized.ConvTranspose2d(
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