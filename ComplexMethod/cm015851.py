def test_remove_no_ops(self):
        def matmul_with_op(x, y, fn):
            return fn(x @ y)

        foo_opt = torch.compile(matmul_with_op)

        # test no-op
        fns = (
            lambda x: x + torch.zeros([256, 256], dtype=torch.float32, device=x.device),
            lambda x: x - torch.zeros([256, 256], dtype=torch.float32, device=x.device),
            lambda x: x * torch.ones([256, 256], dtype=torch.float32, device=x.device),
            lambda x: x / torch.ones([256, 256], dtype=torch.float32, device=x.device),
        )

        inps = [torch.rand([256, 256], device=self.device) for _ in range(2)]

        for fn in fns:
            out, source_codes = run_and_get_code(foo_opt, inps[0], inps[1], fn)
            self.assertEqual(out, matmul_with_op(inps[0], inps[1], fn))

            atol, rtol = None, None
            if self.device == "cpu":
                FileCheck().check_not("cpp_fused").run(source_codes[0])
            else:
                FileCheck().check_not("triton.jit").run(source_codes[0])

        # test dtype conversion
        for lowp_dtype in [torch.float16, torch.bfloat16]:
            if not self.is_dtype_supported(lowp_dtype):
                continue
            inps = [
                torch.rand([256, 256], device=self.device, dtype=lowp_dtype)
                for _ in range(2)
            ]
            for fn in fns:
                out, source_codes = run_and_get_code(foo_opt, inps[0], inps[1], fn)
                self.assertEqual(
                    out, matmul_with_op(inps[0], inps[1], fn), atol=atol, rtol=rtol
                )

            # test broadcasted shape bail
            fn = lambda x: x + torch.zeros(  # noqa: E731
                [256, 256, 256], dtype=lowp_dtype, device=self.device
            )
            out, source_codes = run_and_get_code(foo_opt, inps[0], inps[1], fn)
            self.assertEqual(
                out, matmul_with_op(inps[0], inps[1], fn), atol=atol, rtol=rtol
            )