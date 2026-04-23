def test_linear_with_pointwise(
        self, batch_size, in_features, out_features, bias, epilogue, dtype
    ):
        class M(torch.nn.Module):
            def __init__(self, bias, epilogue, other):
                super().__init__()
                self.linear = torch.nn.Linear(in_features, out_features, bias)
                self.epilogue = _get_epilogue(epilogue, other)

            def forward(self, x):
                return self.epilogue(self.linear(x))

        counters.clear()
        v = torch.randn(batch_size, in_features).to(dtype=dtype)
        u = torch.randn(batch_size, out_features).to(dtype=dtype)
        mod = M(bias=bias, epilogue=epilogue, other=u).to(dtype=dtype).eval()
        with verify(dtype) as (atol, rtol):
            self.common(mod, (v,), atol=atol, rtol=rtol)
        self.assertEqual(counters["inductor"]["cpp_templated_kernel_counter"], 1)
        if (
            (
                (
                    dtype == torch.bfloat16
                    and torch.ops.mkldnn._is_mkldnn_bf16_supported()
                )
                or (
                    dtype == torch.float16
                    and torch.ops.mkldnn._is_mkldnn_fp16_supported()
                )
                or (
                    dtype == torch.float32
                    and not dynamo_config.assume_static_by_default
                )
            )
            and epilogue != "mul"
            and epilogue != "div"
            or (
                dtype in (torch.float16, torch.bfloat16)
                and epilogue == "add"
                and not bias
            )
        ):
            # Several scenarios where epilogue fusion is not counted in:
            # 1. For bfloat16, the epilogue fusion is part of the template,
            #    not fused via scheduler. This will also be true for float16 when
            #    hardware has the float16 instruction. And this will also be true
            #    for float32 dynamic mode. The exception is mul or div fusion
            #    which is not supported for oneDNN linear.
            # 2. For bfloat16/float16, when oneDNN linear is not applied, linear w/o bias
            #    plus epilogue add is treated as linear w/ bias.
            self.assertEqual(counters["inductor"]["cpp_epilogue_fusion_counter"], 0)
        else:
            self.assertEqual(counters["inductor"]["cpp_epilogue_fusion_counter"], 1)