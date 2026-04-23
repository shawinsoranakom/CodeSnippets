def _test_conv_base(self, dim):
        conv_module = {1: torch.nn.Conv1d, 2: torch.nn.Conv2d, 3: torch.nn.Conv3d}
        input_shapes = {1: (224,), 2: (224, 224), 3: (55, 55, 55)}
        options = itertools.product([True, False], [True, False], [1, 2], [1, 4])
        for train, bias, dilation, groups in options:
            N = torch.randint(3, 10, (1,)).item()
            M = torch.randint(1, 3, (1,)).item() * groups
            C = torch.randint(1, 3, (1,)).item() * groups
            x_shape = (N, C) + input_shapes[dim]
            x = torch.randn(x_shape, dtype=torch.float32)
            conv = conv_module[dim](in_channels=C,
                                    out_channels=M,
                                    kernel_size=3,
                                    stride=2,
                                    padding=1,
                                    dilation=dilation,
                                    bias=bias,
                                    groups=groups).float()
            x1 = x.clone()
            x2 = x.clone().to_mkldnn()
            if not train:
                mkldnn_conv = mkldnn_utils.to_mkldnn(copy.deepcopy(conv))
            elif train and dim != 1:
                # TODO: enable conv1d training.
                x1.requires_grad_()
                x2.requires_grad_()
                mkldnn_conv = copy.deepcopy(conv)
            with torch.backends.mkldnn.flags(enabled=False):
                y_aten = conv(x1)
                if train and dim != 1:
                    loss1 = y_aten.sum()
                    loss1.backward()
            if not train or (train and dim != 1):
                y_mkldnn = mkldnn_conv(x2).to_dense()
                if self.precision != 0:
                    self.assertEqual(y_aten, y_mkldnn, atol=self.precision, rtol=self.precision)
                else:
                    self.assertEqual(y_aten, y_mkldnn)
            if not train:
                self._test_serialization(mkldnn_conv, (x.to_mkldnn(),))
                self._test_tracing(mkldnn_conv, (x.to_mkldnn(),))
            elif dim != 1:
                loss2 = y_mkldnn.sum()
                loss2.backward()
                self.assertTrue(x2.grad.is_mkldnn)
                self.assertEqual(x1.grad, x2.grad.to_dense())
                self.assertEqual(conv.weight.grad,
                                 mkldnn_conv.weight.grad,
                                 atol=1e-3,
                                 rtol=1e-3)
                if bias:
                    self.assertEqual(conv.bias.grad, mkldnn_conv.bias.grad)