def test_grouped_linear_epilogue(
        self,
        batch_size,
        in_features,
        out_features,
        input_3d,
        bias,
        epilogue,
        loop_ordering_after_fusion,
    ):
        class M(torch.nn.Module):
            def __init__(self, in_feature, out_feature, bias, epilogue):
                super().__init__()
                self.linear0 = torch.nn.Linear(in_feature, out_feature, bias=bias[0])
                self.linear1 = torch.nn.Linear(in_feature, out_feature, bias=bias[1])
                self.epilogue0 = epilogue[0]
                self.epilogue1 = epilogue[1]

            def forward(self, x):
                res0 = self.linear0(x)
                res1 = self.linear1(x)
                if self.epilogue0 == "silu" and self.epilogue1 == "mul":
                    return torch.nn.functional.silu(res0) * res1
                else:
                    if self.epilogue0 == "relu":
                        res0 = torch.nn.functional.relu(res0)
                    if self.epilogue1 == "relu":
                        res1 = torch.nn.functional.relu(res1)
                    return res0, res1

        dtypes = []
        if torch.ops.mkldnn._is_mkldnn_bf16_supported():
            dtypes.append(torch.bfloat16)
        if torch.ops.mkldnn._is_mkldnn_fp16_supported():
            dtypes.append(torch.float16)
        for dtype in dtypes:
            if input_3d and dtype == torch.float16:
                # Reduce the number of test cases
                continue
            torch._dynamo.reset()
            torch._inductor.metrics.reset()
            counters.clear()
            mod = M(in_features, out_features, bias, epilogue).eval()
            B = (2, batch_size) if input_3d else (batch_size,)
            v = torch.randn(*B, in_features).to(dtype)
            with (
                verify(dtype) as (atol, rtol),
                torch.autocast(device_type="cpu", dtype=dtype),
                torch.no_grad(),
                inductor_config.patch(
                    {"loop_ordering_after_fusion": loop_ordering_after_fusion}
                ),
            ):
                self.common(mod, (v,), atol=atol, rtol=rtol)
            self.assertEqual(counters["inductor"]["cpp_grouped_gemm_template"], 1)
            if any(e != "none" for e in epilogue):
                self.assertGreater(
                    counters["inductor"]["cpp_epilogue_fusion_counter"], 0
                )