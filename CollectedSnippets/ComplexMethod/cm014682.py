def test_blockwise_mxfp8_nvfp4_error_messages(self, device, recipe) -> None:
        if recipe == "mxfp4" and SM120OrLater:
            raise unittest.SkipTest("MXFP4 on CUDA only supported on B200/B300")
        M, K, N = (1024, 512, 2048)
        BLOCK_SIZE_K = 16 if recipe == "nvfp4" else 32
        BLOCK_SIZE_MN = 128
        fill_value = 0.5
        scale_dtype = torch.float8_e4m3fn if recipe == "nvfp4" else torch.float8_e8m0fnu

        x = torch.full((M, K), fill_value, device=device)
        y = torch.full((N, K), fill_value, device=device)

        if recipe == "mxfp8":
            x_lowp = x.to(e4m3_type)
            y_lowp = y.to(e4m3_type).t()
        else:  # nvfp4 #mxfp4
            x_lowp = _bfloat16_to_float4_e2m1fn_x2(x.bfloat16())
            y_lowp = _bfloat16_to_float4_e2m1fn_x2(y.bfloat16()).t()

        num_k_blocks = ceil_div(K, BLOCK_SIZE_K)
        padded_num_k_blocks = ceil_div(num_k_blocks, 4) * 4
        expected_a_size = BLOCK_SIZE_MN * ceil_div(M, BLOCK_SIZE_MN) * padded_num_k_blocks
        expected_b_size = BLOCK_SIZE_MN * ceil_div(N, BLOCK_SIZE_MN) * padded_num_k_blocks

        block = (
            ScalingType.BlockWise1x16
            if recipe == "nvfp4"
            else ScalingType.BlockWise1x32
        )
        if torch.version.hip:
            swizzle = SwizzleType.NO_SWIZZLE
        else:
            swizzle = SwizzleType.SWIZZLE_32_4_4

        # Test wrong scale tensor size for scale_a with correct dtype
        with self.assertRaisesRegex(
            ValueError,
            f".*For Block[W,w]ise.*scaling.*scale_a should have {expected_a_size} "
            f"elements.*"
            ,
        ):
            incorrect_size_a = torch.ones(expected_a_size - 1, device=device, dtype=scale_dtype)
            correct_size_b = torch.ones(expected_b_size, device=device, dtype=scale_dtype)

            scaled_mm_wrap(
                x_lowp,
                y_lowp,
                scale_a=incorrect_size_a,
                scale_recipe_a=block,
                scale_b=correct_size_b,
                scale_recipe_b=block,
                swizzle_a=swizzle,
                swizzle_b=swizzle,
                out_dtype=torch.bfloat16,
            )

        # Test wrong scale tensor size for scale_b with correct dtype
        with self.assertRaisesRegex(
            ValueError,
            f"For Block[W,w]ise.*scaling.*scale_b should have {expected_b_size} "
            f"elements.*"
            ,
        ):
            correct_size_a = torch.ones(expected_a_size, device=device, dtype=scale_dtype)
            incorrect_size_b = torch.ones(expected_b_size + 1, device=device, dtype=scale_dtype)
            scaled_mm_wrap(
                x_lowp,
                y_lowp,
                scale_a=correct_size_a,
                scale_recipe_a=block,
                scale_b=incorrect_size_b,
                scale_recipe_b=block,
                swizzle_a=swizzle,
                swizzle_b=swizzle,
                out_dtype=torch.bfloat16,
            )

        # Test non-contiguous scale tensors with correct dtype
        with self.assertRaisesRegex(
            ValueError,
            "For Block[W,w]ise.*scaling.*both scales should be contiguous"
            ,
        ):
            non_contiguous_a = torch.ones(expected_a_size * 2, device=device, dtype=scale_dtype)[::2]
            contiguous_b = torch.ones(expected_b_size, device=device, dtype=scale_dtype)
            scaled_mm_wrap(
                x_lowp,
                y_lowp,
                scale_a=non_contiguous_a,
                scale_b=contiguous_b,
                out_dtype=torch.bfloat16,
            )