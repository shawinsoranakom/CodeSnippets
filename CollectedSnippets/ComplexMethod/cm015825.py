def test_linear_binary(self, device="cpu"):
        self.device = device

        class M(torch.nn.Module):
            def __init__(self, binary_fn, in_channels, out_channels, bias, **kwargs):
                super().__init__()
                self.linear = torch.nn.Linear(
                    in_channels, out_channels, bias=bias, **kwargs
                )
                self.binary_fn = binary_fn

            def forward(self, x, y):
                x = self.linear(x)
                x = self.binary_fn(x, y.clone())
                return x

        dtypes = []
        if is_mkldnn_bf16_supported(self.device):
            dtypes.append(torch.bfloat16)
        if is_mkldnn_fp16_supported(self.device):
            dtypes.append(torch.float16)
        if torch.backends.mkldnn.matmul.fp32_precision in ["bf16", "tf32"]:
            dtypes.append(torch.float32)
        options = itertools.product(
            binary_list, [[2, 3, 10], [2, 10]], [True, False], dtypes
        )
        out_feature = 30

        for binary_fn, input_shape, bias, dtype in options:
            metrics.reset()
            if (
                dtype != torch.float32
                and torch.backends.mkldnn.matmul.fp32_precision == "tf32"
            ):
                continue

            def matcher_check_fn():
                self.assertEqual(
                    counters["inductor"][
                        "mkldnn_conv_binary_unary_fusion_matcher_nodes"
                    ],
                    0 if TEST_ACL else 2,
                )
                reshape_linear_reshape_match_nodes = 3 if len(input_shape) == 3 else 0
                self.assertEqual(
                    counters["inductor"]["mkldnn_reshape_linear_reshape_matcher_nodes"],
                    reshape_linear_reshape_match_nodes,
                )
                self.assertEqual(
                    counters["inductor"]["mkldnn_linear_weight_pack_matcher_count"], 1
                )

            mod = M(binary_fn, input_shape[-1], out_feature, bias).eval()
            v = torch.randn(input_shape)
            other = torch.randn(input_shape[:-1] + [out_feature]).to(dtype)
            self._test_common(
                mod,
                (
                    v,
                    other,
                ),
                matcher_check_fn,
                check_autocast=dtype,
            )
            # only generated 1 kernel for "to_dtype"
            expected_kernel_count = 2 if TEST_ACL else 1
            if dtype == torch.float32:
                # In BF32, input is float32, will not generate kernel for "to_dtype"
                expected_kernel_count -= 1
            self.assertEqual(metrics.generated_kernel_count, expected_kernel_count)