def test_eager_vs_compiled_bitwise(self, case_idx):
        """Verify eager and compiled produce bitwise identical results."""
        tc = TEST_CASES[case_idx]
        if not torch.version.hip and torch.cuda.get_device_capability() < (
            tc.min_sm // 10,
            tc.min_sm % 10,
        ):
            self.skipTest(f"Requires SM{tc.min_sm}+")

        # Native bf16 conversion instruction not available before gfx950.
        if (
            torch.version.hip
            and tc.name == "add_bf16_native"
            and evaluate_gfx_arch_within(
                [
                    *MI200_ARCH,
                    *MI300_ARCH,
                    *NAVI_ARCH,
                ]
            )
        ):
            self.skipTest("Requires gfx950+")

        inputs = tc.input_gen_fn()

        def fn(*args):
            return inline_asm_elementwise(
                *args,
                asm_str=tc.asm_str,
                constraints=tc.constraints,
                dtype=tc.dtype,
                pack=tc.pack,
            )

        # This test always runs torch.compile(inductor); Inductor needs Triton for CUDA.
        if not has_triton():
            self.skipTest("Requires Triton")

        torch._dynamo.reset()
        compiled_result = torch.compile(fn, backend="inductor")(*inputs)

        if tc.compile_only:
            expected = tc.approx_fn(*inputs)
            self.assertEqual(
                compiled_result.float(), expected.float(), atol=1e-5, rtol=1e-5
            )
        else:
            eager_result = fn(*inputs)
            self.assertEqual(eager_result, compiled_result)