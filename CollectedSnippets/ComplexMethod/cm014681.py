def test_passed_swizzle_arrays(self, device) -> None:
        # Ensure that incorrectly-sized swizzle arrays are caught
        M, N, K = 128, 128, 128

        # MXFP8: swizzle=[SWIZZLE_32_4_4]
        x = torch.randn(M, K, device=device).to(torch.float8_e4m3fn)
        w = torch.randn(N, K, device=device).to(torch.float8_e4m3fn)

        x_scale = torch.full((M, K // 32), 1., dtype=torch.float8_e8m0fnu, device=device)
        w_scale = torch.full((N, K // 32), 1., dtype=torch.float8_e8m0fnu, device=device)

        # No swizzle passed - must fail on swizzle_a
        with self.assertRaisesRegex(
            ValueError,
            "swizzle_a and swizzle_b must each have 1 value"
            if torch.version.hip
            else "swizzle_a must have 1 value, got 0",
        ):
            _ = torch.nn.functional.scaled_mm(
                x,
                w.t(),
                x_scale,
                ScalingType.BlockWise1x32,
                w_scale,
                ScalingType.BlockWise1x32,
            )

        # swizzle_a passed, not b, must fail on swizzle_b
        with self.assertRaisesRegex(
            ValueError,
            "swizzle_a and swizzle_b must each have 1 value"
            if torch.version.hip
            else "swizzle_b must have 1 value, got 0",
        ):
            _ = torch.nn.functional.scaled_mm(
                x,
                w.t(),
                x_scale,
                ScalingType.BlockWise1x32,
                w_scale,
                ScalingType.BlockWise1x32,
                swizzle_a=SwizzleType.SWIZZLE_32_4_4,
            )
        if torch.version.hip:
            with self.assertRaisesRegex(
                ValueError,
                "swizzle_a and swizzle_b must both be NO_SWIZZLE",
            ):
                _ = torch.nn.functional.scaled_mm(
                    x,
                    w.t(),
                    x_scale,
                    ScalingType.BlockWise1x32,
                    w_scale,
                    ScalingType.BlockWise1x32,
                    swizzle_a=SwizzleType.NO_SWIZZLE,
                    swizzle_b=SwizzleType.SWIZZLE_32_4_4,
                )

        # NVFP4 two-level: swizzle=[SWIZZLE_32_4_4, NO_SWIZZLE]
        x = _bfloat16_to_float4_e2m1fn_x2(x.to(torch.bfloat16))
        w = _bfloat16_to_float4_e2m1fn_x2(w.to(torch.bfloat16))

        x_scale = torch.full((M, K // 16), 1., dtype=torch.float8_e4m3fn, device=device)
        w_scale = torch.full((N, K // 16), 1., dtype=torch.float8_e4m3fn, device=device)

        global_scale = torch.full((1, ), 1., dtype=torch.float, device=device)

        # No swizzles passed - must fail on swizzle_a
        with self.assertRaisesRegex(
            NotImplementedError if torch.version.hip else ValueError,
            "NVFP4 scaling not supported on ROCM"
            if torch.version.hip
            else "swizzle_a must have 2 values, got 0",
        ):
            _ = torch.nn.functional.scaled_mm(
                x,
                w.t(),
                [x_scale, global_scale],
                [ScalingType.BlockWise1x16, ScalingType.TensorWise],
                [w_scale, global_scale],
                [ScalingType.BlockWise1x16, ScalingType.TensorWise],
            )

        # Not enough swizzles passed - must fail on swizzle_a
        with self.assertRaisesRegex(
            NotImplementedError if torch.version.hip else ValueError,
            "NVFP4 scaling not supported on ROCM"
            if torch.version.hip
            else "swizzle_a must have 2 values, got 1",
        ):
            _ = torch.nn.functional.scaled_mm(
                x,
                w.t(),
                [x_scale, global_scale],
                [ScalingType.BlockWise1x16, ScalingType.TensorWise],
                [w_scale, global_scale],
                [ScalingType.BlockWise1x16, ScalingType.TensorWise],
                swizzle_a=[SwizzleType.SWIZZLE_32_4_4, ],
            )

        # Not enough swizzles passed to b - must fail on swizzle_b
        with self.assertRaisesRegex(
            NotImplementedError if torch.version.hip else ValueError,
            "NVFP4 scaling not supported on ROCM"
            if torch.version.hip
            else "swizzle_b must have 2 values, got 1",
        ):
            _ = torch.nn.functional.scaled_mm(
                x,
                w.t(),
                [x_scale, global_scale],
                [ScalingType.BlockWise1x16, ScalingType.TensorWise],
                [w_scale, global_scale],
                [ScalingType.BlockWise1x16, ScalingType.TensorWise],
                swizzle_a=[SwizzleType.SWIZZLE_32_4_4, SwizzleType.NO_SWIZZLE],
                swizzle_b=[SwizzleType.SWIZZLE_32_4_4, ],
            )