def test_scaled_mm_block_wise_numerics(self, output_dtype, lhs_block, rhs_block, M, N, K, test_case):
        """
        subsume test_scaled_mm_vs_emulated_block_wise for random inputs, random scales,
        do some other functional tests as well.

        # Inputs (as generated are):
        #   A: [M, K]
        #   B: [N, K]
        # then scales are, for the 3 combinations:
        #   1x128 x 1x128:
        #     As: [M, K // 128], stride: [1, M] -> scale.t().contiguous().t()
        #     Bs: [N, K // 128], stride: [1, N] -> scale.t().contiguous().t()
        #   1x128 x 128x128
        #     L4 = round_up(K // 128, 4)
        #     As: [M, K // 128], stride: [1, M]   -> scale.t().contiguous().t()
        #     Bs: [L4, N // 128], stride: [1, L4] -> scale.t()
        #   128x128 x 1x128
        #     L4 = round_up(K // 128, 4)
        #     As: [L4, M // 128], stride: [1, L4]
        #     Bs: [N, K // 128], stride: [1, N]
        """
        torch.manual_seed(42)

        def _adjust_lhs_scale(x_fp8, x_scales, lhs_block):
            M, K = x_fp8.shape
            x_scales_original = x_scales.clone()
            # 1x128 blocks need scales to be outer-dim-major
            if lhs_block == 1:
                x_scales = x_scales.t().contiguous().t()
                lhs_recipe = ScalingType.BlockWise1x128
                if not (x_scales.shape[0] == M and x_scales.shape[1] == K // 128):
                    raise AssertionError(f"{x_scales.shape=}")
                if not (x_scales.stride(0) == 1 and x_scales.stride(1) in [1, M]):
                    raise AssertionError(f"{x_scales.stride=}")
                x_hp = hp_from_1x128(x_fp8, x_scales_original)
            else:
                lhs_recipe = ScalingType.BlockWise128x128
                x_scales, pad_amount = _pad_128x128_scales(x_scales)
                # scales in [M // 128, L4] -> [L4, M // 128]
                x_scales = x_scales.t()
                x_hp = hp_from_128x128(x_fp8, x_scales_original)

            return x_hp, lhs_recipe, x_scales, x_scales_original

        def _adjust_rhs_scale(y_fp8, y_scales, rhs_block):
            N, K = y_fp8.shape
            y_scales_original = y_scales.clone()

            if rhs_block == 1:
                y_scales = y_scales.t().contiguous().t()
                rhs_recipe = ScalingType.BlockWise1x128
                if not (y_scales.shape[0] == N and y_scales.shape[1] == K // 128):
                    raise AssertionError(f"{y_scales.shape=}")
                if not (y_scales.stride(0) == 1 and y_scales.stride(1) in [1, N]):
                    raise AssertionError(f"{y_scales.stride=}")
                y_hp = hp_from_1x128(y_fp8, y_scales_original)
            else:
                rhs_recipe = ScalingType.BlockWise128x128
                y_scales, pad_amount = _pad_128x128_scales(y_scales)
                # Scale in [N // 128, L4] -> [L4, N // 128]
                y_scales = y_scales.t()
                y_hp = hp_from_128x128(y_fp8, y_scales_original)

            return y_hp, rhs_recipe, y_scales, y_scales_original

        def _build_lhs(x, lhs_block):
            M, K = x.shape

            x_fp8, x_scales = tensor_to_scale_block(x, e4m3_type, lhs_block, 128)
            x_scales_original = x_scales

            x_hp, x_recipe, x_scales, x_scales_original = _adjust_lhs_scale(x_fp8, x_scales, lhs_block)

            return x_hp, x_recipe, x_fp8, x_scales, x_scales_original

        def _build_rhs(y, rhs_block):
            N, K = y.shape

            y_fp8, y_scales = tensor_to_scale_block(y, e4m3_type, rhs_block, 128)
            y_hp, y_recipe, y_scales, y_scales_original = _adjust_rhs_scale(y_fp8, y_scales, rhs_block)

            return y_hp, y_recipe, y_fp8, y_scales, y_scales_original

        def _run_test(x_hp, x_recipe, x_fp8, x_scales, x_scales_original,
                      y_hp, y_recipe, y_fp8, y_scales, y_scales_original):

            # Calculate actual F8 mm
            out_scaled_mm = scaled_mm_wrap(
                x_fp8,
                y_fp8.t(),
                scale_a=x_scales.reciprocal(),
                scale_recipe_a=x_recipe,
                # Note: No more .t() on scale_b, not necessary.
                scale_b=y_scales.reciprocal(),
                scale_recipe_b=y_recipe,
                out_dtype=output_dtype,
            )

            # Calculate emulated F8 mm
            out_emulated = mm_float8_emulated_block(
                x_fp8,
                x_scales_original,
                y_fp8.t(),
                y_scales_original.t(),
                output_dtype
            )

            cosine_sim = torch.nn.functional.cosine_similarity(
                out_emulated.flatten().float(), (x @ y.t()).flatten().float(), dim=0
            )
            self.assertGreaterEqual(float(cosine_sim), 0.999)

            cosine_sim = torch.nn.functional.cosine_similarity(
                out_scaled_mm.flatten().float(), out_emulated.flatten().float(), dim=0
            )
            self.assertGreaterEqual(float(cosine_sim), 0.999)

            if output_dtype in {torch.bfloat16, torch.float16}:
                atol, rtol = 6e-1, 7e-2
            else:
                atol, rtol = 7e-1, 2e-3

            self.assertEqual(out_scaled_mm, out_emulated.to(output_dtype), atol=atol, rtol=rtol)

            # One last check against the full-precision reference, to ensure we
            # didn't mess up the scaling itself and made the test trivial.
            cosine_sim = torch.nn.functional.cosine_similarity(
                out_scaled_mm.flatten().float(), (x @ y.t()).flatten().float(), dim=0
            )
            self.assertGreaterEqual(float(cosine_sim), 0.999)

        def _build_constant_scale(t, block, val):
            M, K = t.shape

            if block == 1:
                scale_shape = M, K // 128
            else:
                scale_shape = M // 128, K // 128

            scale = torch.full(scale_shape, val, device='cuda')

            return scale

        def hp_to_scaled(t, scale, block):
            if block == 1:
                return hp_to_1x128(t, scale)
            else:
                return hp_to_128x128(t, scale)

        e4m3_type = torch.float8_e4m3fn

        if test_case == "x_eye_b_eye":
            if M != K or M != N:
                return unittest.skip("a_eye_b_eye only defined for M = N = K")
            x = torch.eye(M, device='cuda')
            y = torch.eye(M, device='cuda')

            x_hp, x_recipe, x_fp8, x_scales, x_scales_original = _build_lhs(x, lhs_block)
            y_hp, y_recipe, y_fp8, y_scales, y_scales_original = _build_lhs(y, rhs_block)
        elif test_case == "x_ones_y_ones_calc_scales":
            x = torch.full((M, K), 1.0, device='cuda')
            y = torch.full((N, K), 1.0, device='cuda')

            x_hp, x_recipe, x_fp8, x_scales, x_scales_original = _build_lhs(x, lhs_block)
            y_hp, y_recipe, y_fp8, y_scales, y_scales_original = _build_lhs(y, rhs_block)
        elif test_case in ["x_ones_y_ones_set_scales", "x_ones_y_ones_modify_scales"]:
            x = torch.full((M, K), 1.0, device='cuda')
            y = torch.full((N, K), 1.0, device='cuda')

            x_scales = _build_constant_scale(x, lhs_block, 1.)
            y_scales = _build_constant_scale(y, rhs_block, 1.)

            if "modify" in test_case:
                x_scales[0, 0] = 4.
                y_scales[-1, -1] = 4.

            x_fp8 = hp_to_scaled(x, x_scales, lhs_block)
            y_fp8 = hp_to_scaled(y, y_scales, rhs_block)

            x_hp, x_recipe, x_scales, x_scales_original = _adjust_lhs_scale(x_fp8, x_scales, lhs_block)
            y_hp, y_recipe, y_scales, y_scales_original = _adjust_rhs_scale(y_fp8, y_scales, rhs_block)
        elif test_case == "data_random_scales_one":
            x = torch.randint(0, 255, (M, K), device='cuda', dtype=torch.uint8).to(torch.bfloat16)
            y = torch.randint(0, 255, (N, K), device='cuda', dtype=torch.uint8).to(torch.bfloat16)

            x_scales = _build_constant_scale(x, lhs_block, 1.)
            y_scales = _build_constant_scale(y, rhs_block, 1.)

            x_fp8 = hp_to_scaled(x, x_scales, lhs_block)
            y_fp8 = hp_to_scaled(y, y_scales, rhs_block)

            x_hp, x_recipe, x_scales, x_scales_original = _adjust_lhs_scale(x_fp8, x_scales, lhs_block)
            y_hp, y_recipe, y_scales, y_scales_original = _adjust_rhs_scale(y_fp8, y_scales, rhs_block)
        elif test_case == "data_random_calc_scales":
            # Note: Old test_scaled_mm_vs_emulated_block_wise test case
            x = torch.randn(M, K, device="cuda", dtype=output_dtype)
            y = torch.randn(N, K, device="cuda", dtype=output_dtype) * 1e-3

            x_hp, x_recipe, x_fp8, x_scales, x_scales_original = _build_lhs(x, lhs_block)
            y_hp, y_recipe, y_fp8, y_scales, y_scales_original = _build_lhs(y, rhs_block)
        else:
            raise ValueError("Unknown test-case passed")

        _run_test(x_hp, x_recipe, x_fp8, x_scales, x_scales_original,
                  y_hp, y_recipe, y_fp8, y_scales, y_scales_original)