def test_blockwise_mxfp8_nvfp4_mxfp4_numerics(self, test_case_name, fast_accum, mkn, recipe) -> None:
        if torch.version.hip and recipe == "nvfp4":
            raise unittest.SkipTest("nvfp4 not supported on ROCm, skipping")
        if (recipe == "nvfp4" or recipe == "mxfp4") and fast_accum:
            raise unittest.SkipTest("fast_accum not supported in nvfp4/mxfp4 cublas gemm, skipping")
        if recipe == "mxfp4" and SM120OrLater:
            raise unittest.SkipTest("MXFP4 on CUDA only supported on B200/B300")

        device = "cuda"
        M, K, N = mkn
        if recipe == "nvfp4" and K % 32 != 0:
            raise unittest.SkipTest("K must be divisible by 32 for nvfp4 cublas gemm, skipping")

        if torch.version.hip:
            if not (M % 16 == 0 and K % 128 == 0 and N % 16 == 0):
                raise unittest.SkipTest("M and N must be multiples of 16 and K must be multiple of 128 on ROCm, skipping")

        fp4_scaling_dtype = torch.float8_e8m0fnu if recipe == "mxfp4" else torch.float8_e4m3fn
        BLOCK_SIZE = 16 if recipe == "nvfp4" else 32

        if K % BLOCK_SIZE != 0:
            raise unittest.SkipTest(f"K ({K}) must be divisible by BLOCK_SIZE ({BLOCK_SIZE}), skipping")

        require_exact_match = True
        approx_match_sqnr_target = 22.0

        if test_case_name == "a_eye_b_eye":
            if not ((M == K) and (M == N)):
                raise unittest.SkipTest("this test is only defined for M == K == N, skipping")
            A_ref = torch.eye(M, device=device, dtype=torch.bfloat16)
            B_ref = torch.eye(M, device=device, dtype=torch.bfloat16)

            if recipe == "mxfp8":
                A = A_ref.to(torch.float8_e4m3fn)
                B = B_ref.to(torch.float8_e4m3fn)
                A_scale = torch.full((M, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=torch.float8_e8m0fnu)
                B_scale = torch.full((N, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=torch.float8_e8m0fnu)
            else:  # nvfp4 # mxfp4
                A = _bfloat16_to_float4_e2m1fn_x2(A_ref)
                B = _bfloat16_to_float4_e2m1fn_x2(B_ref)
                A_scale = torch.full((M, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=fp4_scaling_dtype)
                B_scale = torch.full((N, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=fp4_scaling_dtype)

        elif test_case_name == "a_ones_b_ones":
            A_ref = torch.ones(M, K, device=device, dtype=torch.bfloat16)
            B_ref = torch.ones(N, K, device=device, dtype=torch.bfloat16)

            if recipe == "mxfp8":
                A = A_ref.to(torch.float8_e4m3fn)
                B = B_ref.to(torch.float8_e4m3fn)
                A_scale = torch.full((M, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=torch.float8_e8m0fnu)
                B_scale = torch.full((N, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=torch.float8_e8m0fnu)
            else:  # nvfp4 # mxfp4
                A = _bfloat16_to_float4_e2m1fn_x2(A_ref)
                B = _bfloat16_to_float4_e2m1fn_x2(B_ref)
                A_scale = torch.full((M, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=fp4_scaling_dtype)
                B_scale = torch.full((N, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=fp4_scaling_dtype)

        elif test_case_name == "a_ones_modified_b_ones":
            A_ref = torch.ones(M, K, device=device, dtype=torch.bfloat16)
            B_ref = torch.ones(N, K, device=device, dtype=torch.bfloat16)
            A_ref[1][0:BLOCK_SIZE] = 2

            if recipe == "mxfp8":
                A = A_ref.to(torch.float8_e4m3fn)
                B = B_ref.to(torch.float8_e4m3fn)
                A_scale = torch.full((M, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=torch.float8_e8m0fnu)
                B_scale = torch.full((N, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=torch.float8_e8m0fnu)
            else:  # nvfp4 # mxfp4
                A = _bfloat16_to_float4_e2m1fn_x2(A_ref)
                B = _bfloat16_to_float4_e2m1fn_x2(B_ref)
                A_scale = torch.full((M, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=fp4_scaling_dtype)
                B_scale = torch.full((N, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=fp4_scaling_dtype)

        elif test_case_name == "a_ones_b_ones_modified":
            A_ref = torch.ones(M, K, device=device, dtype=torch.bfloat16)
            B_ref = torch.ones(N, K, device=device, dtype=torch.bfloat16)
            B_ref[1][0:BLOCK_SIZE] = 2

            if recipe == "mxfp8":
                A = A_ref.to(torch.float8_e4m3fn)
                B = B_ref.to(torch.float8_e4m3fn)
                A_scale = torch.full((M, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=torch.float8_e8m0fnu)
                B_scale = torch.full((N, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=torch.float8_e8m0fnu)
            else:  # nvfp4 # mxfp4
                A = _bfloat16_to_float4_e2m1fn_x2(A_ref)
                B = _bfloat16_to_float4_e2m1fn_x2(B_ref)
                A_scale = torch.full((M, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=fp4_scaling_dtype)
                B_scale = torch.full((N, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=fp4_scaling_dtype)

        elif test_case_name == "a_scale_modified_b_ones":
            A_ref = torch.ones(M, K, device=device, dtype=torch.bfloat16)
            B_ref = torch.ones(N, K, device=device, dtype=torch.bfloat16)

            if recipe == "mxfp8":
                A = A_ref.to(torch.float8_e4m3fn)
                B = B_ref.to(torch.float8_e4m3fn)
                A_scale = torch.full((M, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=torch.float8_e8m0fnu)
                B_scale = torch.full((N, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=torch.float8_e8m0fnu)
                A_ref[1][0:BLOCK_SIZE] = 4
                A[1][0:BLOCK_SIZE] = 2
                A_scale[1][0] = 2
            else:  # nvfp4 # mxfp4
                A = _bfloat16_to_float4_e2m1fn_x2(A_ref)
                B = _bfloat16_to_float4_e2m1fn_x2(B_ref)
                A_scale = torch.full((M, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=fp4_scaling_dtype)
                B_scale = torch.full((N, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=fp4_scaling_dtype)
                A_ref[1][0:BLOCK_SIZE] = 4
                A.view(torch.uint8)[1][0:(BLOCK_SIZE // 2)] = 0b01000100
                A_scale[1][0] = 2

        elif test_case_name == "a_ones_b_scale_modified":
            A_ref = torch.ones(M, K, device=device, dtype=torch.bfloat16)
            B_ref = torch.ones(N, K, device=device, dtype=torch.bfloat16)

            if recipe == "mxfp8":
                A = A_ref.to(torch.float8_e4m3fn)
                B = B_ref.to(torch.float8_e4m3fn)
                A_scale = torch.full((M, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=torch.float8_e8m0fnu)
                B_scale = torch.full((N, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=torch.float8_e8m0fnu)
                B_ref[1][0:BLOCK_SIZE] = 4
                B[1][0:BLOCK_SIZE] = 2
                B_scale[1][0] = 2
            else:  # nvfp4 # mxfp4
                A = _bfloat16_to_float4_e2m1fn_x2(A_ref)
                B = _bfloat16_to_float4_e2m1fn_x2(B_ref)
                A_scale = torch.full((M, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=fp4_scaling_dtype)
                B_scale = torch.full((N, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=fp4_scaling_dtype)
                B_ref[1][0:BLOCK_SIZE] = 4
                B.view(torch.uint8)[1][0:(BLOCK_SIZE // 2)] = 0b01000100
                B_scale[1][0] = 2

        elif test_case_name == "data_random_scales_one":
            require_exact_match = False

            if recipe == "mxfp8":
                # scales all-ones, element data random while being exactly representable in float8_e4m3fn
                # generate integers in [0, 255] and interpret as float8_e4m3fn
                A_ref = torch.randint(0, 255, (M, K), device=device, dtype=torch.uint8).view(torch.float8_e4m3fn).to(torch.bfloat16)
                B_ref = torch.randint(0, 255, (N, K), device=device, dtype=torch.uint8).view(torch.float8_e4m3fn).to(torch.bfloat16)
                # modification: don't allow NaN values
                A_ref[torch.isnan(A_ref)] = 0
                B_ref[torch.isnan(B_ref)] = 0
                A = A_ref.to(torch.float8_e4m3fn)
                B = B_ref.to(torch.float8_e4m3fn)
                A_scale = torch.full((M, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=torch.float8_e8m0fnu)
                B_scale = torch.full((N, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=torch.float8_e8m0fnu)
            else:  # nvfp4 # mxfp4
                # scales all-ones, element data random while being exactly representable in float4_e2m1fn_x2
                # generate integers in [0, 16] and cast to bfloat16
                A_ref = _floatx_unpacked_to_f32(
                    torch.randint(0, 16, (M, K), device=device, dtype=torch.uint8),
                    FP4_EBITS,
                    FP4_MBITS
                ).bfloat16()
                B_ref = _floatx_unpacked_to_f32(
                    torch.randint(0, 16, (N, K), device=device, dtype=torch.uint8),
                    FP4_EBITS,
                    FP4_MBITS
                ).bfloat16()
                A = _bfloat16_to_float4_e2m1fn_x2(A_ref)
                B = _bfloat16_to_float4_e2m1fn_x2(B_ref)
                A_scale = torch.full((M, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=fp4_scaling_dtype)
                B_scale = torch.full((N, ceil_div(K, BLOCK_SIZE)), 1.0, device=device, dtype=fp4_scaling_dtype)

        elif test_case_name == "data_random_scales_from_data":
            if not K % BLOCK_SIZE == 0:
                raise unittest.SkipTest(f"this test is only defined for K a multiple of {BLOCK_SIZE}, skipping")
            require_exact_match = False
            # random data, scales from data
            A_ref = torch.randn((M, K), device=device, dtype=torch.bfloat16) * 1000
            B_ref = torch.randn((N, K), device=device, dtype=torch.bfloat16) * 1000

            if recipe == "mxfp8":
                # Calculate scales based on the inputs
                A_scale = data_to_mx_scale(A_ref, BLOCK_SIZE, recipe)
                B_scale = data_to_mx_scale(B_ref, BLOCK_SIZE, recipe)
                max_val = F8E4M3_MAX_VAL
                min_val = -1 * max_val
                A = (A_ref.reshape(-1, BLOCK_SIZE) / A_scale.reshape(M * ceil_div(K, BLOCK_SIZE), 1).float()).reshape(M, K)
                A = A.clamp(min=min_val, max=max_val).to(torch.float8_e4m3fn)
                B = (B_ref.reshape(-1, BLOCK_SIZE) / B_scale.reshape(N * ceil_div(K, BLOCK_SIZE), 1).float()).reshape(N, K)
                B = B.clamp(min=min_val, max=max_val).to(torch.float8_e4m3fn)
            else:  # nvfp4 # mxfp4
                if recipe == "mxfp4":
                    A_scale = data_to_mx_scale(A_ref, BLOCK_SIZE, recipe)
                    B_scale = data_to_mx_scale(B_ref, BLOCK_SIZE, recipe)
                else:
                    A_scale = data_to_nvfp4_scale(A_ref, BLOCK_SIZE)
                    B_scale = data_to_nvfp4_scale(B_ref, BLOCK_SIZE)
                max_val = FP4_MAX_VAL
                min_val = -1 * max_val

                A = (A_ref.reshape(-1, BLOCK_SIZE) / A_scale.reshape(M * ceil_div(K, BLOCK_SIZE), 1).bfloat16()).reshape(M, K)
                A = A.clamp(min=min_val, max=max_val)
                A = _bfloat16_to_float4_e2m1fn_x2(A)
                B = (B_ref.reshape(-1, BLOCK_SIZE) / B_scale.reshape(N * ceil_div(K, BLOCK_SIZE), 1).bfloat16()).reshape(N, K)
                B = B.clamp(min=min_val, max=max_val)
                B = _bfloat16_to_float4_e2m1fn_x2(B)

                approx_match_sqnr_target = 15 if recipe == "mxfp4" else 15.8

        C_ref = A_ref @ B_ref.t()

        # convert to swizzled format
        if not torch.version.hip:
            A_scale = to_blocked(A_scale)
            B_scale = to_blocked(B_scale)

        C = scaled_mm_wrap(
            A,
            B.t(),
            A_scale,
            B_scale,
            out_dtype=torch.bfloat16,
            use_fast_accum=fast_accum,
        )

        if require_exact_match:
            torch.testing.assert_close(C, C_ref, atol=0, rtol=0)
        else:
            sqnr = compute_error(C_ref, C)
            if sqnr.item() <= approx_match_sqnr_target:
                raise AssertionError(f"sqnr {sqnr.item()} should be > {approx_match_sqnr_target}")