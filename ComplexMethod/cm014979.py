def _test_conv_deconv_lower_precision_base(self, dim, conv_module, dtype):
        input_shapes = {1: (224,), 2: (224, 224), 3: (55, 55, 55)}
        options = itertools.product([True, False], [1, 2], [1, 4])
        for bias, dilation, groups in options:
            N = torch.randint(1, 3, (1,)).item()
            M = torch.randint(1, 3, (1,)).item() * groups
            C = torch.randint(1, 3, (1,)).item() * groups
            x_shape = (N, C) + input_shapes[dim]
            x = torch.randn(x_shape, dtype=torch.float32)
            # TODO: remove this when group depthwise is supported:
            if conv_module in [torch.nn.ConvTranspose1d, torch.nn.ConvTranspose2d,
                               torch.nn.ConvTranspose3d] and groups > 1 and C == groups:
                continue
            conv = conv_module(in_channels=C,
                               out_channels=M,
                               kernel_size=3,
                               stride=2,
                               padding=1,
                               dilation=dilation,
                               bias=bias,
                               groups=groups).float()
            x_lower = x.to(dtype=dtype)
            if (dtype == torch.bfloat16 and torch.ops.mkldnn._is_mkldnn_bf16_supported()) or \
               (dtype == torch.half and torch.ops.mkldnn._is_mkldnn_fp16_supported()):
                mkldnn_conv = mkldnn_utils.to_mkldnn(copy.deepcopy(conv))
                mkldnn_conv_lower = mkldnn_utils.to_mkldnn(copy.deepcopy(conv), dtype)
                y = mkldnn_conv(x.to_mkldnn()).to_dense()
                y_lower = mkldnn_conv_lower(x_lower.to_mkldnn()).to_dense(torch.float32)
                self.assertEqual(y, y_lower, atol=1e-1, rtol=1e-3)
            else:
                msg = {
                    torch.bfloat16: r"bf16 path needs the cpu support avx_ne_convert or avx512bw, avx512vl and avx512dq",
                    torch.half: r"fp16 path needs the cpu support avx_ne_convert or avx512_fp16",
                }
                with self.assertRaisesRegex(RuntimeError, msg[dtype]):
                    mkldnn_conv_lower = mkldnn_utils.to_mkldnn(copy.deepcopy(conv), dtype)
                    y_lower = mkldnn_conv_lower(x_lower.to_mkldnn()).to_dense(torch.float32)
            # test thnn impl
            conv_lower = copy.deepcopy(conv).to(dtype=dtype)
            conv_ref = copy.deepcopy(conv_lower).float()
            with torch.backends.mkldnn.flags(enabled=False):
                x_ref = x_lower.clone().float().detach().requires_grad_()
                x_lower.requires_grad_()
                y = conv_ref(x_ref)
                y_lower = conv_lower(x_lower).float()
                self.assertEqual(y, y_lower, atol=5e-2, rtol=5e-3)