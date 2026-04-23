def _test_conv_transpose_unary_base(self, dim=4):
        if dim != 4 and dim != 5:
            raise AssertionError(f"Expected dim to be 4 or 5, got {dim}")

        class M(torch.nn.Module):
            def __init__(
                self,
                unary_fn,
                **kwargs,
            ):
                super().__init__()
                if dim == 4:
                    self.conv_transpose = torch.nn.ConvTranspose2d(
                        3, 16, 3, stride=2, padding=1
                    )
                else:
                    self.conv_transpose = torch.nn.ConvTranspose3d(
                        3, 16, 3, stride=2, padding=1
                    )
                self.unary_fn = unary_fn

            def forward(self, x):
                x = self.conv_transpose(x)
                return self.unary_fn(x)

        dtypes = [
            torch.float,
        ]
        if is_mkldnn_bf16_supported(self.device):
            dtypes.append(torch.bfloat16)
        if is_mkldnn_fp16_supported(self.device):
            dtypes.append(torch.float16)

        cl_format = torch.channels_last if dim == 4 else torch.channels_last_3d
        options = itertools.product(
            unary_list,
            [torch.contiguous_format, cl_format],
            dtypes,
        )

        for unary_fn, memory_format, dtype in options:
            metrics.reset()
            if dim == 4:
                x_shape = (1, 3, 28, 28)
            else:
                x_shape = (1, 3, 17, 28, 28)
            mod = M(unary_fn).eval()

            v = torch.randn(x_shape, dtype=torch.float32).to(
                memory_format=memory_format
            )

            def matcher_check_fn():
                match_nodes = unary_list[unary_fn]
                if dtype in (
                    torch.float16,
                    torch.bfloat16,
                ) and self._check_unary_is_decomposed(unary_fn):
                    # Has extra dtype conversion nodes for autocast.
                    match_nodes += 2
                self.assertEqual(
                    counters["inductor"]["mkldnn_unary_fusion_matcher_nodes"],
                    0 if TEST_ACL else match_nodes,
                )
                self.assertEqual(
                    counters["inductor"]["mkldnn_conv_weight_pack_matcher_count"], 1
                )

            self._test_common(mod, (v,), matcher_check_fn, check_autocast=dtype)
            generated_kernel_count = cal_conv_generated_kernel_number(
                mod, v, dtype, dim, self.device
            )
            self.assertEqual(metrics.generated_kernel_count, generated_kernel_count)