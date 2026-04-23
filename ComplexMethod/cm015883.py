def test_folded_conv_bn_hardswish(self):
        for use_bias, dtype in itertools.product(
            [True, False], [torch.float16, torch.bfloat16, torch.float32]
        ):
            if self.device == "cpu" and dtype == torch.float16:
                continue

            if self.device == GPU_TYPE and dtype == torch.bfloat16 and not SM80OrLater:
                continue

            mod = (
                ConvBNHardswish(3, 32, bias=use_bias, kernel_size=3, stride=2)
                .eval()
                .to(self.device)
                .to(dtype)
            )

            x = torch.rand(3, 3, 32, 32).to(self.device).to(dtype)

            torch._dynamo.reset()
            counters.clear()

            @torch.compile()
            def foo(mod, x):
                return mod(x)

            # TODO - bias is separate kernel right now, we should only unfuse it
            # from conv if it can be fused

            with torch.no_grad():
                out_eager = mod(x)
                out_optimized_for_infernece, code = run_and_get_code(foo, mod, x)

            # we unfuse the conv bias, but it should only have one constant in the kernel
            if self.device == "cuda":
                FileCheck().check_not(".run(").check("conv").check(".run(").check_same(
                    "frozen_param"
                ).check_not("frozen_param").check_next("return").run(code[0])

            self.assertEqual(
                out_optimized_for_infernece, out_eager, atol=1e-2, rtol=1e-2
            )
            self.assertEqual(counters["inductor"]["binary_folding"], 4)