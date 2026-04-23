def test_scaled_mm_vs_emulated(self, base_dtype, x_cm, y_cm, device):
        # Blackwell (SM_10) supports all possible layout permutations, while Hopper only TN
        if torch.cuda.is_available():
            if (x_cm, y_cm) != (True, False) and torch.cuda.get_device_properties(0).major != 10:
                raise unittest.SkipTest("Unsupported layout on the architecture")
        torch.manual_seed(42)
        input_dtype = e4m3_type
        output_dtype = base_dtype
        compare_type = torch.float32

        M, N, K = 16, 32, 16
        x = torch.randn(M, K, device=device, dtype=base_dtype) if x_cm else torch.randn(K, M, device=device, dtype=base_dtype).t()
        y = torch.randn(K, N, device=device, dtype=base_dtype) if y_cm else torch.randn(N, K, device=device, dtype=base_dtype).t()

        x_scale = tensor_to_scale(x, input_dtype).float()
        y_scale = tensor_to_scale(y, input_dtype).float()


        x_fp8 = to_fp8_saturated(x * x_scale, input_dtype)
        y_fp8 = to_fp8_saturated(y * y_scale, input_dtype)

        # Calculate actual F8 mm
        out_scaled_mm = scaled_mm_wrap(
            x_fp8,
            y_fp8,
            scale_a=x_scale.reciprocal(),
            scale_b=y_scale.reciprocal(),
            out_dtype=output_dtype
        )

        # Calculate emulated F8 mm
        out_emulated = mm_float8_emulated(
            x_fp8,
            x_scale,
            y_fp8,
            y_scale,
            output_dtype
        )

        if output_dtype != base_dtype:
            out_scaled_mm = out_scaled_mm.to(compare_type)
            out_scaled_mm = out_scaled_mm / tensor_to_scale(out_scaled_mm, input_dtype)

            out_emulated = out_emulated.to(compare_type)
            out_emulated = out_emulated / tensor_to_scale(out_emulated, input_dtype)

        if base_dtype in {torch.bfloat16, torch.float16}:
            atol, rtol = 7e-2, 7e-2
        else:
            atol, rtol = 3e-3, 3e-3

        torch.testing.assert_close(out_scaled_mm, out_emulated, atol=atol, rtol=rtol)