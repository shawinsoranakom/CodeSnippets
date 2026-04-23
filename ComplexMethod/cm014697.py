def test_addmm_baddmm_dtype_overload(self, input_dtype, M, N, K, batch_size, broadcast_self, high_precision_self, backend):
        if torch.version.hip:
            msg = "accuracy regression in hipblas and hipblaslt in ROCm 7.0 for certain shapes"
            if input_dtype == torch.bfloat16 and N == 1 and K == 32 and batch_size:
                raise unittest.SkipTest(msg)
            if input_dtype == torch.bfloat16 and N == 1 and K == 64 and batch_size:
                raise unittest.SkipTest(msg)
            if input_dtype == torch.float16 and M == 32 and N == 1 and K == 64 and batch_size == 1:
                raise unittest.SkipTest(msg)
            if input_dtype == torch.float16 and M == 64 and N == 1 and K == 64 and batch_size == 1:
                raise unittest.SkipTest(msg)

        device = "cuda"
        dtype = input_dtype
        with blas_library_context(backend):
            def create_inputs(B, broadcast_self):
                if B is None:
                    a = torch.randn(M, K, device=device, dtype=dtype)
                    b = torch.randn(K, N, device=device, dtype=dtype)
                    c_shape = (M, N) if not broadcast_self else (N)
                    c = torch.randn(c_shape, device=device, dtype=dtype)
                else:
                    a = torch.randn(B, M, K, device=device, dtype=dtype)
                    b = torch.randn(B, K, N, device=device, dtype=dtype)
                    c_shape = (B, M, N) if not broadcast_self else (N)
                    c = torch.randn(c_shape, device=device, dtype=dtype)

                return a, b, c

            a, b, c = create_inputs(batch_size, broadcast_self)

            a_fp32, b_fp32, c_fp32 = a.to(torch.float32), b.to(torch.float32), c.to(torch.float32)

            output_dtypes = [torch.float32]

            if input_dtype != torch.float32:
                output_dtypes.append(input_dtype)

            for output_dtype in output_dtypes:
                # Catch edge case of incompat with bfloat16 and major version < 8
                if input_dtype == torch.bfloat16 and not PLATFORM_SUPPORTS_BF16:
                    if output_dtype == torch.bfloat16:
                        continue

                    if batch_size:
                        with self.assertRaises(RuntimeError):
                            torch.baddbmm(c, a, b, out_dtype=output_dtype)
                    else:
                        with self.assertRaises(RuntimeError):
                            torch.addmm(c, a, b, out_dtype=output_dtype)
                else:
                    if c.dtype != output_dtype and high_precision_self:
                        c = c.to(output_dtype)
                    if batch_size:
                        out = torch.baddbmm(c, a, b, out_dtype=output_dtype)
                        if output_dtype == torch.float32:
                            baseline = torch.baddbmm(c_fp32, a_fp32, b_fp32)
                        else:
                            baseline = torch.baddbmm(c, a, b)
                        # test out variant
                        out_ten = torch.full_like(out, float("nan"))
                        torch.baddbmm(c, a, b, out_dtype=output_dtype, out=out_ten)
                    else:
                        out = torch.addmm(c, a, b, out_dtype=output_dtype)
                        if output_dtype == torch.float32:
                            baseline = torch.addmm(c_fp32, a_fp32, b_fp32)
                        else:
                            baseline = torch.addmm(c, a, b)
                        # test out variant
                        out_ten = torch.full_like(out, float("nan"))
                        torch.addmm(c, a, b, out_dtype=output_dtype, out=out_ten)

                    self.assertEqual(out.dtype, output_dtype)
                    self.assertEqual(out_ten.dtype, output_dtype)
                    torch.testing.assert_close(out, baseline, atol=1e-3, rtol=1e-3)
                    torch.testing.assert_close(out_ten, out, atol=0, rtol=0)