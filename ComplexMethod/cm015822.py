def _test_conv_binary_base(self, dim=4):
        if dim != 4 and dim != 5:
            raise AssertionError(f"Expected dim to be 4 or 5, got {dim}")

        class M(torch.nn.Module):
            def __init__(
                self,
                binary_fn,
                has_relu,
                **kwargs,
            ):
                super().__init__()
                if dim == 4:
                    self.conv1 = torch.nn.Conv2d(3, 16, kernel_size=3, stride=1)
                    self.conv2 = torch.nn.Conv2d(3, 16, kernel_size=3, stride=1)
                else:
                    self.conv1 = torch.nn.Conv3d(3, 16, kernel_size=3, stride=1)
                    self.conv2 = torch.nn.Conv3d(3, 16, kernel_size=3, stride=1)
                self.binary_fn = binary_fn
                self.has_relu = has_relu

            def forward(self, x):
                x1 = self.conv1(x)
                x2 = self.conv2(x)
                if has_relu:
                    return self.binary_fn(x1, x2).relu()
                else:
                    return self.binary_fn(x1, x2)

        dtypes = [
            torch.float,
        ]
        if is_mkldnn_bf16_supported(self.device):
            dtypes.append(torch.bfloat16)
        if is_mkldnn_fp16_supported(self.device):
            dtypes.append(torch.float16)
        cl_format = torch.channels_last if dim == 4 else torch.channels_last_3d
        test_memory_format = [torch.contiguous_format, cl_format]
        options = itertools.product(
            binary_list,
            [True, False],
            test_memory_format,
            dtypes,
        )

        for (
            binary_fn,
            has_relu,
            memory_format,
            dtype,
        ) in options:
            if (
                dtype != torch.float32
                and torch.backends.mkldnn.matmul.fp32_precision == "tf32"
            ):
                continue
            metrics.reset()
            if dim == 4:
                x_shape = (1, 3, 56, 56)
            else:
                x_shape = (1, 3, 20, 56, 56)
            mod = M(binary_fn, has_relu).eval()
            v = (
                torch.randn(x_shape, dtype=torch.float32, requires_grad=True)
                .add(1)
                .to(memory_format=memory_format)
            )

            def matcher_check_fn():
                match_nodes = binary_list[binary_fn][1]
                if has_relu:
                    match_nodes += 1
                self.assertEqual(
                    counters["inductor"][
                        "mkldnn_conv_binary_unary_fusion_matcher_nodes"
                    ],
                    0 if TEST_ACL else match_nodes,
                )
                self.assertEqual(
                    counters["inductor"]["mkldnn_conv_weight_pack_matcher_count"], 2
                )

            self._test_common(mod, (v,), matcher_check_fn, check_autocast=dtype)
            generated_kernel_count = cal_conv_generated_kernel_number(
                mod, v, dtype, dim, self.device
            )
            self.assertEqual(metrics.generated_kernel_count, generated_kernel_count)