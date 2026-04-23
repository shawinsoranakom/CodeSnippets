def test_scaled_mm_vs_emulated_row_wise(self, base_dtype, shapes, device):
        M, K, N = shapes
        # Fp32 out_dtype is only supported by cuBLAS, which however only started
        # shipping row-wise kernels in CUDA 12.9, and only for sm90+.
        if base_dtype is torch.float32:
            if torch.version.hip:
                raise unittest.SkipTest("hipblaslt rowwise _scaled_mm only supports BFloat16")
            if torch.cuda.is_available() and _get_torch_cuda_version() < (12, 9):
                raise unittest.SkipTest("Need CUDA 12.9+ for row-wise fp8 w/ cuBLAS")
            if torch.cuda.is_available() and torch.cuda.get_device_capability() < (9, 0):
                raise unittest.SkipTest("Need sm90+ for row-wise fp8 w/ cuBLAS")

        if base_dtype is torch.float16:
            if torch.version.hip:
                raise unittest.SkipTest("hipblaslt rowwise _scaled_mm only supports BFloat16")
            if torch.cuda.is_available() and torch.cuda.get_device_capability() < (9, 0):
                raise unittest.SkipTest("Need sm90+ for row-wise fp8 w/ cuBLAS")

        torch.manual_seed(42)
        input_dtype = e4m3_type
        output_dtype = base_dtype

        x = torch.randn(M, K, device=device, dtype=base_dtype)
        y = torch.randn(N, K, device=device, dtype=base_dtype).t()
        bias = None
        if base_dtype in {torch.bfloat16, torch.float16}:
            bias = torch.randn((N,), device=device, dtype=base_dtype)

        x_scales = tensor_to_scale(x, input_dtype, dim=1).float()
        y_scales = tensor_to_scale(y, input_dtype, dim=0).float()

        x_fp8 = to_fp8_saturated(x * x_scales, e4m3_type)
        y_fp8 = to_fp8_saturated(y * y_scales, e4m3_type)

        def test():
            # Calculate actual F8 mm
            out_scaled_mm = scaled_mm_wrap(
                x_fp8,
                y_fp8,
                scale_a=x_scales.reciprocal(),
                scale_b=y_scales.reciprocal(),
                out_dtype=output_dtype,
                bias=bias
            )

            # Calculate emulated F8 mm
            out_emulated = mm_float8_emulated(
                x_fp8, x_scales, y_fp8, y_scales, output_dtype, bias
            )

            if base_dtype in {torch.bfloat16, torch.float16}:
                atol, rtol = 7e-2, 7e-2
            else:
                atol, rtol = 2e-3, 2e-3

            self.assertEqual(out_scaled_mm, out_emulated, atol=atol, rtol=rtol)

            cosine_sim = torch.nn.functional.cosine_similarity(
                out_emulated.flatten().float(), out_scaled_mm.flatten().float(), dim=0
            )
            self.assertGreaterEqual(float(cosine_sim), 0.999)

        # only cuBLAS supports rowwise with fp32 output and cuBLAS only supports
        # rowwise on SM 9.0
        if torch.cuda.is_available() and torch.cuda.get_device_capability() != (9, 0) and output_dtype == torch.float:
            with self.assertRaisesRegex(
                ValueError,
                "Only bf16 and fp16 high precision output types are supported for row-wise scaling."
            ):
                test()
        else:
            test()