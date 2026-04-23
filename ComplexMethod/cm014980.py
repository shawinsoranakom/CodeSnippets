def _test_conv_transpose_base(self, dim):
        conv_module = {
            1: torch.nn.ConvTranspose1d,
            2: torch.nn.ConvTranspose2d,
            3: torch.nn.ConvTranspose3d
        }
        input_shapes = {1: (55,), 2: (28, 28), 3: (14, 14, 14)}
        options = itertools.product([True, False], [True, False], [1, 2], [1, 4])
        for train, bias, dilation, groups in options:
            N = torch.randint(3, 10, (1,)).item()
            M = torch.randint(1, 3, (1,)).item() * groups
            C = torch.randint(1, 3, (1,)).item() * groups
            x_shape = (N, C) + input_shapes[dim]
            data = torch.randn(x_shape, dtype=torch.float32)
            # conv: mkldnn transpose conv fp32
            # conv_ref: thnn transpose conv fp32
            conv = conv_module[dim](in_channels=C,
                                    out_channels=M,
                                    kernel_size=3,
                                    stride=1,
                                    padding=1,
                                    dilation=dilation,
                                    bias=bias,
                                    groups=groups).to(dtype=torch.float32)
            x = data.clone()
            x_ref = x.clone()
            if train:
                x.requires_grad_()
                x_ref.requires_grad_()

            conv_ref = copy.deepcopy(conv)
            with torch.backends.mkldnn.flags(enabled=False):
                y_ref = conv_ref(x_ref)
                if train:
                    y_ref.sum().backward()

            y = conv(x)
            if train:
                y.sum().backward()

            if self.precision != 0:
                self.assertEqual(y, y_ref, atol=self.precision, rtol=self.precision)
            else:
                self.assertEqual(y, y_ref)

            if train:
                self.assertEqual(x.grad, x_ref.grad)
                self.assertEqual(conv.weight.grad,
                                 conv_ref.weight.grad,
                                 atol=1e-3,
                                 rtol=1e-3)
                if bias:
                    self.assertEqual(conv.bias.grad, conv_ref.bias.grad)