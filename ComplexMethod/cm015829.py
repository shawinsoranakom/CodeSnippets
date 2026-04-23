def test_tensorwise_scaling(
        self,
        dtype: torch.dtype,
        shape: str,
        has_bias: bool,
        use_fast_accum: bool,
        persistent_matmul: bool,
        device,
    ):
        if dtype is torch.float32 and has_bias:
            self.skipTest("bias is not supported when output dtype is float32")
        dtype_float8 = torch.float8_e4m3fn
        dtype_float8 = _fix_fp8_dtype_for_rocm(dtype_float8, device)

        shape = [int(dim) for dim in shape.split(",")]
        M, K, N = shape  # Matmul Y = X [M, K] x W [N, K]
        # input and output dtypes of _scaled_mm do not need to be the same, but
        # typically in a model they are
        x = torch.randn(M, K, dtype=dtype, device=device)
        w = torch.randn(N, K, dtype=dtype, device=device)
        bias = None
        if has_bias:
            bias = torch.randn(N, device=device, dtype=torch.bfloat16)

        if "xpu" in device and use_fast_accum:
            self.skipTest("XPU does not support use_fast_accum=True for now")

        # quantize weight (prior to inference)
        w_fp8, w_inverse_scale = _quantize_tensorwise(w, dtype_float8)
        w_t_fp8 = w_fp8.t()

        # quantize input x
        x_fp8, x_inverse_scale = _quantize_tensorwise(x, dtype_float8)

        def linear(x_fp8, x_inverse_scale, w_t_fp8, w_inverse_scale, bias):
            y = torch._scaled_mm(
                x_fp8,
                w_t_fp8,
                x_inverse_scale,
                w_inverse_scale,
                bias,
                out_dtype=dtype,
                use_fast_accum=use_fast_accum,
            )
            return y

        y_eager = linear(
            x_fp8,
            x_inverse_scale,
            w_t_fp8,
            w_inverse_scale,
            bias,
        )
        with config.patch({"triton.enable_persistent_tma_matmul": persistent_matmul}):
            linear_compiled = torch.compile(
                linear, backend="inductor", mode="max-autotune"
            )
            y_compiled = linear_compiled(
                x_fp8,
                x_inverse_scale,
                w_t_fp8,
                w_inverse_scale,
                bias,
            )
            self.assertEqual(y_eager.dtype, dtype)
            self.assertEqual(y_compiled.dtype, dtype)
            # depending on the kernel config (BLOCK_M size, etc) selected during Inductor
            # autotuning for the compiled case, the results can be different because of
            # the way blocks of results are accumulated (float addition not associative), so
            # setting a small absolute tolerance in these tests
            if dtype == torch.bfloat16:
                self.assertEqual(y_eager, y_compiled, rtol=5e-2, atol=0.07)
            else:
                self.assertEqual(y_eager, y_compiled, rtol=1e-2, atol=0.05)