def _test_qconv_fp8_helper(self, nd, pointwise_post_op):
        # nd = 1,2,3 -> conv1d/2d/3d
        if pointwise_post_op.binary_attr != "none":
            # Only conv2d supports binary post op
            if nd != 2:
                raise AssertionError(f"Expected nd == 2, got {nd}")
        groups_list = [1, 3]
        input_channels_per_group = 2
        output_channels_per_group = 2
        length = 4
        kernel = 3
        stride = 1
        pad = 1
        dilation = 1
        use_bias_list = [False, True]
        use_channelwise_list = [False, True]
        output_dtype_list = [None, torch.float32, torch.bfloat16]
        options = itertools.product(groups_list, use_bias_list, use_channelwise_list, output_dtype_list)
        for groups, use_bias, use_channelwise, output_dtype in options:
            if output_dtype is not None and not (use_bias and use_channelwise):
                # Remove some test combination to reduce UT test time
                continue
            conv_mod = getattr(torch.nn, f"Conv{nd}d")(
                input_channels_per_group * groups,
                output_channels_per_group * groups,
                kernel,
                stride,
                pad,
                dilation,
                groups,
            )
            qconv = (
                torch.ops.onednn.qconv_pointwise
                if pointwise_post_op.binary_attr == "none"
                else torch.ops.onednn.qconv2d_pointwise.binary
            )
            qconv_prepack = torch.ops.onednn.qconv_prepack
            self._test_qconv_impl_cpu_tensor_fp8(
                qconv,
                qconv_prepack,
                conv_mod,
                input_channels_per_group=input_channels_per_group,
                input_feature_map_shape=(length,) * nd,
                output_channels_per_group=output_channels_per_group,
                groups=groups,
                kernels=[kernel] * nd,
                strides=[stride] * nd,
                pads=[pad] * nd,
                dilations=[dilation] * nd,
                use_bias=use_bias,
                post_op=pointwise_post_op,
                use_channelwise=use_channelwise,
                qconv_output_dtype=output_dtype,
            )