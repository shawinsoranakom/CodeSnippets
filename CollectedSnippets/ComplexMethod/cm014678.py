def test_scaled_mm_vs_emulated_block_wise_verify_small_shapes(
        self, output_dtype, lhs_block, rhs_block, M, N, K
    ):
        torch.manual_seed(42)

        x = torch.randn(M, K, device="cuda", dtype=output_dtype).pow(3)
        y = torch.randn(N, K, device="cuda", dtype=output_dtype).pow(3)

        x_fp8, x_scales = tensor_to_scale_block(x, e4m3_type, lhs_block, 128)
        y_fp8, y_scales = tensor_to_scale_block(y, e4m3_type, rhs_block, 128)

        x_scales_original = x_scales
        y_scales_original = y_scales
        # 1x128 blocks need scales to be outer-dim-major
        if lhs_block == 1:
            x_scales = x_scales.t().contiguous().t()
            lhs_recipe = ScalingType.BlockWise1x128
            if not (x_scales.shape[0] == M and x_scales.shape[1] == K // 128):
                raise AssertionError(f"{x_scales.shape=}")
            if not (x_scales.stride(0) == 1 and x_scales.stride(1) in [1, M]):
                raise AssertionError(f"{x_scales.stride=}")
        else:
            lhs_recipe = ScalingType.BlockWise128x128
            x_scales, pad_amount = _pad_128x128_scales(x_scales)
            # scales in [M // 128, L4] -> [L4, M // 128]
            x_scales = x_scales.t()

        if rhs_block == 1:
            y_scales = y_scales.t().contiguous().t()
            rhs_recipe = ScalingType.BlockWise1x128
            if not (y_scales.shape[0] == N and y_scales.shape[1] == K // 128):
                raise AssertionError(f"{y_scales.shape=}")
            if not (y_scales.stride(0) == 1 and y_scales.stride(1) in [1, N]):
                raise AssertionError(f"{y_scales.stride=}")
        else:
            rhs_recipe = ScalingType.BlockWise128x128
            y_scales, pad_amount = _pad_128x128_scales(y_scales)
            # Scale in [N // 128, L4] -> [L4, N // 128]
            y_scales = y_scales.t()

        # Verify that actual F8 mm doesn't error
        scaled_mm_wrap(
            x_fp8,
            y_fp8.t(),
            scale_a=x_scales,
            scale_recipe_a=lhs_recipe,
            # Note: No more .t() on scale_b, not necessary.
            scale_b=y_scales,
            scale_recipe_b=rhs_recipe,
            out_dtype=output_dtype,
        )

        # Verify that emulated F8 mm doesn't error
        mm_float8_emulated_block(
            x_fp8,
            x_scales_original,
            y_fp8.t(),
            y_scales_original.t(),
            output_dtype
        )