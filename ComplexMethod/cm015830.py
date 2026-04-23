def test_main_loop_scaling(
        self,
        shape: tuple[int, int, int],
        use_fast_accum: bool,
        scaling_block_sizes: tuple[int, int, int, int],
        device,
    ):
        if "xpu" in device and use_fast_accum:
            self.skipTest("XPU does not support use_fast_accum=True for now")
        # Only bf16 output type is supported for non-tensorwise scaling, not fp32
        dtype: torch.dtype = torch.bfloat16
        dtype_float8 = torch.float8_e4m3fn
        dtype_float8 = _fix_fp8_dtype_for_rocm(dtype_float8, device)

        M, N, K = shape  # Matmul Y = X [M, K] x W [N, K]
        x = torch.randn(M, K, dtype=dtype, device=device)
        w = torch.randn(N, K, dtype=dtype, device=device)
        bias = None

        am, ak, bn, bk = scaling_block_sizes

        # quantize weight (prior to inference)
        w_fp8, w_inverse_scale = _quantize_blockwise(
            w, dtype_float8, block_outer=bn, block_inner=bk
        )
        w_t_fp8 = w_fp8.t()
        if (bn, bk) == (1, 128):
            w_inverse_scale = (
                w_inverse_scale.t().contiguous().t().t()
            )  # 1x128 blocks need scales to be outer-dim-major
        else:
            w_inverse_scale = w_inverse_scale.t()  # scale_b should be (1, N)

        # quantize input x
        x_fp8, x_inverse_scale = _quantize_blockwise(
            x, dtype_float8, block_outer=am, block_inner=ak
        )
        if (am, ak) == (1, 128):
            x_inverse_scale = (
                x_inverse_scale.t().contiguous().t()
            )  # 1x128 blocks need scales to be outer-dim-major

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

        # BlockWise1x128 and BlockWise128x128 scaling modes are not compatible with fast_accum
        # Only take this branch on SM90 because other versions xfail everything
        if use_fast_accum and IS_SM90:
            with self.assertRaisesRegex(
                RuntimeError, "scaled_gemm doesn't support fast accum"
            ):
                y_eager = linear(
                    x_fp8,
                    x_inverse_scale,
                    w_t_fp8,
                    w_inverse_scale,
                    bias,
                )
        else:
            y_eager = linear(
                x_fp8,
                x_inverse_scale,
                w_t_fp8,
                w_inverse_scale,
                bias,
            )

        with config.patch(
            {
                "triton.enable_persistent_tma_matmul": True,
                "test_configs.autotune_choice_name_regex": "triton_scaled_mm_device_tma",
                "max_autotune_gemm_backends": "TRITON",
                "max_autotune": True,
            }
        ):
            linear_compiled = torch.compile(
                linear, backend="inductor", mode="max-autotune"
            )
            y_compiled, code = run_and_get_code(
                linear_compiled,
                x_fp8,
                x_inverse_scale,
                w_t_fp8,
                w_inverse_scale,
                bias,
            )

        # Verify that Inductor chooses the correct scaling recipes
        check_scale_recipe_a = (
            ScalingType.BlockWise1x128.value
            if (am, ak) == (1, 128)
            else ScalingType.BlockWise128x128.value
        )
        FileCheck().check(
            f"SCALE_RECIPE_A : tl.constexpr = {check_scale_recipe_a}"
        ).run(code[0])

        check_scale_recipe_b = (
            ScalingType.BlockWise1x128.value
            if (bn, bk) == (1, 128)
            else ScalingType.BlockWise128x128.value
        )
        FileCheck().check(
            f"SCALE_RECIPE_B : tl.constexpr = {check_scale_recipe_b}"
        ).run(code[0])

        self.assertEqual(y_compiled.dtype, dtype)
        if not use_fast_accum:
            self.assertEqual(y_eager.dtype, dtype)
            torch.testing.assert_close(y_eager, y_compiled, rtol=1e-2, atol=0.05)