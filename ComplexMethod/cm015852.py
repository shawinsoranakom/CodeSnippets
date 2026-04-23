def test_dropout3(self):
        if is_mps_backend(self.device) and torch._inductor.config.align_random_eager:
            raise AssertionError(
                "MPS + align_random_eager + dynamic shapes: will pass but force failure for xfail_if_mps"
            )
        m = torch.nn.Sequential(
            torch.nn.Linear(32, 32, bias=False),
            torch.nn.Dropout(),
            torch.nn.Linear(32, 32, bias=False),
            torch.nn.Dropout(),
        ).to(self.device)

        @torch._dynamo.optimize_assert("inductor")
        def run(x):
            return m(x)

        torch._inductor.metrics.generated_kernel_count = 0

        result, (fw_code, bw_code) = run_fw_bw_and_get_code(
            lambda: run(torch.randn([8, 32], device=self.device))
        )

        if (
            is_halide_backend(self.device)
            and not torch._inductor.config.align_random_eager
        ):
            self.assertEqual(fw_code.count("halide_helpers.rand"), 2)
            self.assertEqual(bw_code.count("halide_helpers.rand"), 0)
        elif self.device == GPU_TYPE and not torch._inductor.config.align_random_eager:
            # the load_seed_offset arg can be 1 or non-1; depending on whether
            # the triton signature specializes on 1 vs non-1, you might get 1
            # or 2 kernels. In newer versions of triton, there's no specialization
            # so we get only 1 kernel.
            self.assertEqual(fw_code.count("tl.rand"), 2)
            self.assertEqual(bw_code.count("tl.rand"), 0)
            self.assertEqual(
                torch._inductor.metrics.generated_kernel_count,
                4 if not config.triton.native_matmul else 6,
            )
        else:
            self.assertEqual(
                torch._inductor.metrics.generated_kernel_count,
                4,
            )