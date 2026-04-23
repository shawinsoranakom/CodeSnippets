def test_conv_bn_relu(
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
        dilation,
        padding_mode,
        use_relu,
        eps,
        momentum,
        freeze_bn,
        zero_gamma,
        has_bias,
        use_slow_fusion,
    ):
        input_channels = input_channels_per_group * groups
        output_channels = output_channels_per_group * groups
        dilation_h = dilation_w = dilation

        conv_op = Conv2d(
            input_channels,
            output_channels,
            (kernel_h, kernel_w),
            (stride_h, stride_w),
            (pad_h, pad_w),
            (dilation_h, dilation_w),
            groups,
            has_bias,
            padding_mode,
        ).to(dtype=torch.double)
        bn_op = BatchNorm2d(output_channels, eps, momentum).to(dtype=torch.double)
        relu_op = ReLU()

        cls = ConvBnReLU2d if use_relu else ConvBn2d
        qat_op = cls(
            input_channels,
            output_channels,
            (kernel_h, kernel_w),
            (stride_h, stride_w),
            (pad_h, pad_w),
            (dilation_h, dilation_w),
            groups,
            has_bias,
            padding_mode,
            eps,
            momentum,
            freeze_bn=True,
            qconfig=default_qat_qconfig,
        ).to(dtype=torch.double)
        qat_op._enable_slow_path_for_better_numerical_stability = use_slow_fusion

        # the approximate fusion will not work if bn.weight has 0
        if zero_gamma and use_slow_fusion:
            torch.nn.init.zeros_(qat_op.bn.weight)

        qat_op.apply(torch.ao.quantization.disable_fake_quant)
        if freeze_bn:
            qat_op.apply(torch.ao.nn.intrinsic.qat.freeze_bn_stats)
        else:
            qat_op.apply(torch.ao.nn.intrinsic.qat.update_bn_stats)

        # align inputs and internal parameters
        input = torch.randn(
            batch_size,
            input_channels,
            height,
            width,
            dtype=torch.double,
            requires_grad=True,
        )
        conv_op.weight = torch.nn.Parameter(qat_op.weight.detach())
        if has_bias:
            conv_op.bias = torch.nn.Parameter(qat_op.bias.detach())
        bn_op.running_mean = qat_op.bn.running_mean.clone()
        bn_op.running_var = qat_op.bn.running_var.clone()
        bn_op.weight = torch.nn.Parameter(qat_op.bn.weight.detach())
        bn_op.bias = torch.nn.Parameter(qat_op.bn.bias.detach())

        def compose(functions):
            # functions are reversed for natural reading order
            return reduce(lambda f, g: lambda x: f(g(x)), functions[::-1], lambda x: x)

        if not use_relu:

            def relu_op(x):
                return x

        if freeze_bn:

            def ref_op(x):
                x = conv_op(x)
                x = (x - bn_op.running_mean.reshape([1, -1, 1, 1])) * (
                    bn_op.weight / torch.sqrt(bn_op.running_var + bn_op.eps)
                ).reshape([1, -1, 1, 1]) + bn_op.bias.reshape([1, -1, 1, 1])
                x = relu_op(x)
                return x

        else:
            ref_op = compose([conv_op, bn_op, relu_op])

        input_clone = input.detach().clone().requires_grad_()
        for _ in range(2):
            result_ref = ref_op(input)
            result_actual = qat_op(input_clone)
            self.assertEqual(result_ref, result_actual)

            # backward
            dout = torch.randn(result_ref.size(), dtype=torch.double)
            loss = (result_ref - dout).sum()
            loss.backward()
            input_grad_ref = input.grad.cpu()
            weight_grad_ref = conv_op.weight.grad.cpu()
            gamma_grad_ref = bn_op.weight.grad.cpu()
            beta_grad_ref = bn_op.bias.grad.cpu()
            running_mean_ref = bn_op.running_mean
            running_var_ref = bn_op.running_var
            num_batches_tracked_ref = bn_op.num_batches_tracked
            loss = (result_actual - dout).sum()
            loss.backward()
            input_grad_actual = input_clone.grad.cpu()
            weight_grad_actual = qat_op.weight.grad.cpu()
            gamma_grad_actual = qat_op.bn.weight.grad.cpu()
            beta_grad_actual = qat_op.bn.bias.grad.cpu()
            running_mean_actual = qat_op.bn.running_mean
            running_var_actual = qat_op.bn.running_var
            num_batches_tracked_actual = qat_op.bn.num_batches_tracked
            precision = 1e-10
            self.assertEqual(input_grad_ref, input_grad_actual, atol=precision, rtol=0)
            self.assertEqual(
                weight_grad_ref, weight_grad_actual, atol=precision, rtol=0
            )
            self.assertEqual(gamma_grad_ref, gamma_grad_actual, atol=precision, rtol=0)
            self.assertEqual(beta_grad_ref, beta_grad_actual, atol=precision, rtol=0)
            self.assertEqual(
                num_batches_tracked_ref,
                num_batches_tracked_actual,
                atol=precision,
                rtol=0,
            )
            self.assertEqual(
                running_mean_ref, running_mean_actual, atol=precision, rtol=0
            )
            self.assertEqual(
                running_var_ref, running_var_actual, atol=precision, rtol=0
            )