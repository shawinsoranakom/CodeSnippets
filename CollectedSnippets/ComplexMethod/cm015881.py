def test_mm_concat(self):
        class MM(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()

                self.t1 = torch.nn.Parameter(torch.rand(10, 10))
                self.t2 = torch.nn.Parameter(torch.rand(10, 10))
                self.t3 = torch.nn.Parameter(torch.rand(10, 10))

            def forward(self, x):
                return x @ self.t1, x @ self.t2, x @ self.t3

        class MM2(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()

                self.t1 = torch.nn.Parameter(torch.rand(10, 10))
                self.t2 = torch.nn.Parameter(torch.rand(10, 10))

            def forward(self, x):
                return x @ self.t1, x @ self.t2

        class AddMM(MM):
            def __init__(self) -> None:
                super().__init__()

                self.b1 = torch.nn.Parameter(torch.rand([10]))
                self.b2 = torch.nn.Parameter(torch.rand([10]))
                self.b3 = torch.nn.Parameter(torch.rand([10]))

            def forward(self, x):
                return [
                    aten.addmm(b, x, p)
                    for b, p in [
                        (self.b1, self.t1),
                        (self.b2, self.t2),
                        (self.b3, self.t3),
                    ]
                ]

        for mod_fn in [
            lambda: MM().to(self.device),
            lambda: MM2().to(self.device),
            lambda: AddMM().to(self.device),
        ]:
            mod = mod_fn()
            inp = torch.rand([10, 10]).to(self.device)

            @torch.compile()
            def foo(mod, inp):
                return mod(inp)

            kernel_invoke = "kernel_cpp_0" if self.device == "cpu" else "triton.jit"
            mm_invoke = "mm("
            # https://github.com/pytorch/pytorch/blob/e754611d190b323e53c5d17db0dc39a96687513c/torch/_inductor/fx_passes/mkldnn_fusion.py#L1263
            mkldnn_weight_pack_init = (
                torch.backends.mkldnn.enabled and torch.backends.mkldnn.is_available()
            )
            if self.device == "cpu" and mkldnn_weight_pack_init:
                if torch.ops.mkldnn._is_mkldnn_acl_supported():
                    # for aarch64 with acl supported, use mkldnn weight prepack
                    # https://github.com/pytorch/pytorch/blob/e754611d190b323e53c5d17db0dc39a96687513c/torch/_inductor/fx_passes/mkldnn_fusion.py#L1176-L1184
                    mm_invoke = "mkldnn._linear_pointwise.default("
                elif torch._C.has_mkl:
                    mm_invoke = "mkl_linear.default("

            with torch.no_grad():
                out_eager = mod(inp)
                out, code = run_and_get_code(foo, mod, inp)
                FileCheck().check_not(kernel_invoke).check_count(
                    mm_invoke, count=1, exactly=True
                ).run(code[0])
                self.assertEqual(out_eager, out)

            mod2 = mod_fn()
            mod2.t1 = torch.nn.Parameter(torch.rand([10, 15], device=self.device))
            mod2.t2 = torch.nn.Parameter(torch.rand([10, 20], device=self.device))

            if hasattr(mod2, "b1"):
                mod2.b1 = torch.nn.Parameter(torch.rand([15], device=self.device))
                mod2.b2 = torch.nn.Parameter(torch.rand([20], device=self.device))

            # fused: weights share same dim 0 (in_features), different dim 1 is OK
            with torch.no_grad():
                out_eager = mod2(inp)
                out, code = run_and_get_code(foo, mod2, inp)
                FileCheck().check_not(kernel_invoke).check_count(
                    mm_invoke, count=1, exactly=True
                ).run(code[0])
                self.assertEqual(out_eager, out)