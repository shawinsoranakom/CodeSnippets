def test_mm_bmm_dtype_overload(self, input_dtype, M, N, K, batch_size, backend):
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
            def create_inputs(B=None):
                if B is None:
                    a = torch.randn(M, K, device=device, dtype=dtype)
                    b = torch.randn(K, N, device=device, dtype=dtype)
                else:
                    a = torch.randn(B, M, K, device=device, dtype=dtype)
                    b = torch.randn(B, K, N, device=device, dtype=dtype)
                return a, b

            a, b = create_inputs(batch_size)

            a_fp32, b_fp32 = a.to(torch.float32), b.to(torch.float32)

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
                            torch.bmm(a, b, out_dtype=output_dtype)
                    else:
                        with self.assertRaises(RuntimeError):
                            torch.mm(a, b, out_dtype=output_dtype)
                else:
                    if batch_size:
                        out = torch.bmm(a, b, out_dtype=output_dtype)
                        baseline = torch.bmm(a_fp32, b_fp32) if output_dtype == torch.float32 else torch.bmm(a, b)
                    else:
                        out = torch.mm(a, b, out_dtype=output_dtype)
                        baseline = torch.mm(a_fp32, b_fp32) if output_dtype == torch.float32 else torch.mm(a, b)

                    self.assertEqual(out.dtype, output_dtype)

                    torch.testing.assert_close(out, baseline, atol=1e-3, rtol=1e-3)