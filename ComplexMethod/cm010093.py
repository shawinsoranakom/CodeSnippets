def _check_scaled_mm_sizes_v2(
    self: torch.Tensor,
    mat2: torch.Tensor,
    scale_a: list[torch.Tensor],
    scale_recipe_a: list[ScalingType],
    scale_b: list[torch.Tensor],
    scale_recipe_b: list[ScalingType],
    bias: torch.Tensor | None = None,
    out_dtype: torch.dtype | None = None,
    swizzle_a: list[SwizzleType] | None = None,
    swizzle_b: list[SwizzleType] | None = None,
    use_fast_accum: bool = False,
):
    def is_fp8_or_fp4_type(dtype):
        return dtype in (
            torch.float8_e4m3fn,
            torch.float8_e5m2,
            torch.float8_e4m3fnuz,
            torch.float8_e5m2fnuz,
            torch.float4_e2m1fn_x2,
        )

    def is_fp4_type(dtype):
        return dtype == torch.float4_e2m1fn_x2

    torch._check(
        self.dim() == 2 and mat2.dim() == 2,
        lambda: f"Inputs must be 2D but got self.dim()={self.dim()} and mat2.dim()={mat2.dim()}",
    )
    torch._check(
        is_fp8_or_fp4_type(self.dtype) and is_fp8_or_fp4_type(mat2.dtype),
        lambda: f"Expected both inputs to be fp8 or fp4 types but got self.dtype={self.dtype} and mat2.dtype={mat2.dtype}",
    )

    # Passed tensors:
    # self: [M, K]
    # mat2: [K, N]
    M = self.shape[0]
    K = self.shape[1]
    N = mat2.shape[1]

    # If we're using fp4, using fp4x2 packed format - adjust K appropriately
    if is_fp4_type(self.dtype) and is_fp4_type(mat2.dtype):
        K_packed_multiplier = 2
        K *= K_packed_multiplier

    scale_recipe_a = [ScalingType(si) for si in scale_recipe_a]
    scale_recipe_b = [ScalingType(si) for si in scale_recipe_b]

    if swizzle_a:
        swizzle_a = [SwizzleType(si) for si in swizzle_a]
    else:
        swizzle_a = [
            SwizzleType.NO_SWIZZLE,
        ]
    if swizzle_b:
        swizzle_b = [SwizzleType(si) for si in swizzle_b]
    else:
        swizzle_b = [
            SwizzleType.NO_SWIZZLE,
        ]

    if (
        device_hint(self) == "cuda"
        or device_hint(self) == "xpu"
        or device_hint(self) == "cpu"
    ):

        def is_row_major(stride):
            return stride[0] > stride[1] and stride[1] == 1

        def is_col_major(stride):
            return stride[0] == 1 and stride[1] > 1

        def has_zero_dim(tensor_2d):
            return tensor_2d.size(0) == 0 or tensor_2d.size(1) == 0

        if device_hint(self) != "cpu":
            torch._check(
                is_row_major(self.stride()) or has_zero_dim(self),
                lambda: f"self must be row_major, got stride {self.stride()}",
            )
            torch._check(
                is_col_major(mat2.stride()) or has_zero_dim(mat2),
                lambda: f"mat2 must be col_major, got stride {mat2.stride()}",
            )
            torch._check(
                self.size(1) % 16 == 0,
                lambda: f"Expected self.size(1) to be divisible by 16, but got self.size(1)={self.size(1)}",
            )
            torch._check(
                mat2.size(0) % 16 == 0 and mat2.size(1) % 16 == 0,
                lambda: f"Expected both dimensions of mat2 to be divisible by 16 but got {mat2.shape}",
            )

        def is_tensorwise(recipe_a: list[ScalingType], recipe_b: list[ScalingType]):
            return (
                len(recipe_a) == 1
                and len(recipe_b) == 1
                and recipe_a[0] == ScalingType.TensorWise
                and recipe_b[0] == ScalingType.TensorWise
            )

        def is_rowwise(recipe_a: list[ScalingType], recipe_b: list[ScalingType]):
            return (
                len(recipe_a) == 1
                and len(recipe_b) == 1
                and recipe_a[0] == ScalingType.RowWise
                and recipe_b[0] == ScalingType.RowWise
            )

        def is_mx(recipe_a: list[ScalingType], recipe_b: list[ScalingType]):
            return (
                len(recipe_a) == 1
                and len(recipe_b) == 1
                and recipe_a[0] == ScalingType.BlockWise1x32
                and recipe_b[0] == ScalingType.BlockWise1x32
            )

        def is_nv_single_level(
            recipe_a: list[ScalingType], recipe_b: list[ScalingType]
        ):
            return (
                len(recipe_a) == 1
                and len(recipe_b) == 1
                and recipe_a[0] == ScalingType.BlockWise1x16
                and recipe_b[0] == ScalingType.BlockWise1x16
            )

        def is_nv(recipe_a: list[ScalingType], recipe_b: list[ScalingType]):
            return (
                len(recipe_a) == 2
                and len(recipe_b) == 2
                and recipe_a[0] == ScalingType.BlockWise1x16
                and recipe_a[1] == ScalingType.TensorWise
                and recipe_b[0] == ScalingType.BlockWise1x16
                and recipe_b[1] == ScalingType.TensorWise
            )

        def is_1x128_1x128(recipe_a: list[ScalingType], recipe_b: list[ScalingType]):
            return (
                len(recipe_a) == 1
                and len(recipe_b) == 1
                and recipe_a[0] == ScalingType.BlockWise1x128
                and recipe_b[0] == ScalingType.BlockWise1x128
            )

        def is_1x128_128x128(recipe_a: list[ScalingType], recipe_b: list[ScalingType]):
            return (
                len(recipe_a) == 1
                and len(recipe_b) == 1
                and recipe_a[0] == ScalingType.BlockWise1x128
                and recipe_b[0] == ScalingType.BlockWise128x128
            )

        def is_128x128_1x128(recipe_a: list[ScalingType], recipe_b: list[ScalingType]):
            return (
                len(recipe_a) == 1
                and len(recipe_b) == 1
                and recipe_a[0] == ScalingType.BlockWise128x128
                and recipe_b[0] == ScalingType.BlockWise1x128
            )

        # Given scaling types, check input dimensions

        if is_tensorwise(scale_recipe_a, scale_recipe_b):
            # TensorWise
            torch._check(
                scale_a[0].numel() == 1
                and scale_b[0].numel() == 1
                and scale_a[0].dtype == torch.float32
                and scale_b[0].dtype == torch.float32,
                lambda: "For Tensorwise scaling, both scale_a and scale_b must be single element float (fp32) tensors",
            )
        elif is_rowwise(scale_recipe_a, scale_recipe_b):
            torch._check(
                scale_a[0].shape[0] == M
                and scale_a[0].numel() == M
                and scale_a[0].dtype == torch.float32
                and scale_b[0].numel() == N
                and scale_b[0].dtype == torch.float32,
                lambda: (
                    f"For Rowwise scaling, scale_a must have {self.shape[0]} elements (got: {scale_a[0].numel()})"
                    f", and scale_b must have {mat2.shape[1]} elements (got: {scale_b[0].numel()})"
                ),
            )
        elif is_1x128_1x128(scale_recipe_a, scale_recipe_b):
            # A, B are fp8, scales are fp32
            # As: [M x K // 128], stride: [1, M]
            # Bs: [N x K // 128], stride: [1, N]
            types_ok = (
                scale_a[0].dtype == torch.float32 and scale_b[0].dtype == torch.float32
            )
            sa = scale_a[0]
            scale_a_ok = (
                sa.shape[0] == M
                and sa.shape[1] == K // 128
                and sa.stride(0) == 1
                and (sa.stride(1) == M or (sa.shape[1] == 1 and sa.stride(1) == 1))
            )
            sb = scale_b[0]
            scale_b_ok = (
                sb.shape[0] == N
                and sb.shape[1] == K // 128
                and sb.stride(0) == 1
                and (sb.stride(1) == N or (sb.shape[1] == 1 and sb.stride(1) == 1))
            )

            torch._check(
                types_ok and scale_a_ok and scale_b_ok,
                lambda: (
                    "For 1x128 x 1x128 blockwise scaling, "
                    f"scale a must have shape [{M}, {K // 128}] (got: {sa.shape}) and stride [1, {M}] (got: {sa.stride})"
                    f"scale b must have shape [{N}, {K // 128}] (got: {sb.shape}) and stride [1, {N}] (got: {sb.stride})"
                ),
            )
        elif is_128x128_1x128(scale_recipe_a, scale_recipe_b):
            # A, B are fp8, scales are fp32
            # L4 = round_up(K // 128, 4)
            # As: [L4 x M // 128], stride: [1, L4]
            # Bs: [N x K // 128], stride: [1, N]
            types_ok = (
                scale_a[0].dtype == torch.float32 and scale_b[0].dtype == torch.float32
            )
            L4 = round_up(K / 128, 4)
            sa = scale_a[0]
            scale_a_ok = (
                sa.shape[0] == L4
                and sa.shape[1] == M // 128
                and sa.stride(0) == 1
                and (sa.stride(1) == L4 or (sa.shape[1] == 1 and sa.stride(1) == 1))
            )
            sb = scale_b[0]
            scale_b_ok = (
                sb.shape[0] == N
                and sb.shape[1] == K // 128
                and sb.stride(0) == 1
                and (sb.stride(1) == N or (sb.shape[1] == 1 and sb.stride(1) == 1))
            )
            torch._check(
                types_ok and scale_a_ok and scale_b_ok,
                lambda: (
                    "For 128x128 x 1x128 blockwise scaling, L4 = {round_up(K / 128, 4)}, "
                    f"scale a must have shape [{L4}, {M // 128}] (got: {sa.shape}) and stride [1, {L4}] (got: {sa.stride})"
                    f"scale b must have shape [{N}, {K // 128}] (got: {sb.shape}) and stride [1, {N}] (got: {sb.stride})"
                ),
            )
        elif is_1x128_128x128(scale_recipe_a, scale_recipe_b):
            # A, B are fp8, scales are fp32
            # L4 = round_up(K // 128, 4)
            # As: [M x K // 128], stride: [1, M]
            # Bs: [L4 x N // 128], stride: [1, L4]
            types_ok = (
                scale_a[0].dtype == torch.float32 and scale_b[0].dtype == torch.float32
            )
            L4 = round_up(K / 128, 4)
            sa = scale_a[0]
            scale_a_ok = (
                sa.shape[0] == M
                and sa.shape[1] == K // 128
                and sa.stride(0) == 1
                and (sa.stride(1) == M or (sa.shape[1] == 1 and sa.stride(1) == 1))
            )
            sb = scale_b[0]
            scale_b_ok = (
                sb.shape[0] == L4
                and sb.shape[1] == N // 128
                and sb.stride(0) == 1
                and (sb.stride(1) == L4 or (sb.shape[1] == 1 and sb.stride(1) == 1))
            )
            torch._check(
                types_ok and scale_a_ok and scale_b_ok,
                lambda: (
                    "For 1x128 x 128x128 blockwise scaling, L4 = {round_up(K / 128, 4)}, "
                    f"scale a must have shape [{M}, {K // 128}] (got: {sa.shape}) and stride [1, {M}] (got: {sa.stride})"
                    f"scale b must have shape [{L4}, {N // 128}] (got: {sb.shape}) and stride [1, {L4}] (got: {sb.stride})"
                ),
            )
        elif is_mx(scale_recipe_a, scale_recipe_b):
            if torch.version.hip:
                # Note(slayton58): These mirror ROCm in ScaledBlas.cpp, but I think they're wrong..
                expected_scale_a_elems = ceil_div(self.shape[0], 32) * self.shape[1]
                expected_scale_b_elems = ceil_div(self.shape[1], 32) * self.shape[0]
                expected_swizzle = SwizzleType.NO_SWIZZLE
            else:
                expected_scale_a_elems = round_up(self.shape[0], 128) * round_up(
                    ceil_div(self.shape[1], 32), 4
                )
                expected_scale_b_elems = round_up(mat2.shape[1], 128) * round_up(
                    ceil_div(self.shape[1], 32), 4
                )
                expected_swizzle = SwizzleType.SWIZZLE_32_4_4
            torch._check(
                scale_a[0].numel() == expected_scale_a_elems
                and scale_a[0].dtype == torch.float8_e8m0fnu
                and scale_b[0].numel() == expected_scale_b_elems
                and scale_b[0].dtype == torch.float8_e8m0fnu
                and swizzle_a[0] == expected_swizzle
                and swizzle_b[0] == expected_swizzle,
                lambda: (
                    f"for MX scaling scale_a must have {expected_scale_a_elems} (got: {scale_a[0].numel()}) "
                    f"and scale_b must have {expected_scale_b_elems} (got: {scale_b[0].numel()}). Scales must "
                    f"have types {torch.float8_e8m0fnu} (for self: {scale_a[0].dtype}, mat_b: {scale_b[0].dtype}) "
                    f"Must have swizzle type {expected_swizzle} (got self: {swizzle_a[0]}, mat_b: {swizzle_b[0]})"
                ),
            )
        elif is_nv_single_level(scale_recipe_a, scale_recipe_b):
            expected_scale_a_elems = round_up(M, 128) * round_up(ceil_div(K, 16), 4)
            expected_scale_b_elems = round_up(N, 128) * round_up(ceil_div(K, 16), 4)
            expected_swizzle = SwizzleType.SWIZZLE_32_4_4
            torch._check(
                scale_a[0].numel() == expected_scale_a_elems
                and scale_a[0].dtype == torch.float8_e4m3fn
                and scale_b[0].numel() == expected_scale_b_elems
                and scale_b[0].dtype == torch.float8_e4m3fn
                and swizzle_a[0] == expected_swizzle
                and swizzle_b[0] == expected_swizzle,
                lambda: (
                    f"for single-level NV scaling scale_a must have {expected_scale_a_elems} (got: {scale_a[0].numel()}) "
                    f"and scale_b must have {expected_scale_b_elems} (got: {scale_b[0].numel()}). Must have "
                    f"swizzle type {expected_swizzle} (got self: {swizzle_a[0]}, mat_b: {swizzle_b[0]})"
                ),
            )
        elif is_nv(scale_recipe_a, scale_recipe_b):
            expected_scale_a_elems = round_up(M, 128) * round_up(ceil_div(K, 16), 4)
            expected_scale_b_elems = round_up(N, 128) * round_up(ceil_div(K, 16), 4)
            expected_swizzle = SwizzleType.SWIZZLE_32_4_4
            torch._check(
                scale_a[0].numel() == expected_scale_a_elems
                and scale_a[0].dtype == torch.float8_e4m3fn
                and scale_a[1].numel() == 1
                and scale_a[1].dtype == torch.float32
                and scale_b[0].numel() == expected_scale_b_elems
                and scale_b[0].dtype == torch.float8_e4m3fn
                and scale_b[1].numel() == 1
                and scale_b[1].dtype == torch.float32
                and swizzle_a[0] == expected_swizzle
                and swizzle_b[0] == expected_swizzle,
                lambda: (
                    f"for NV scaling scale_a must have {expected_scale_a_elems} (got: {scale_a[0].numel()}) "
                    f"and scale_b must have {expected_scale_b_elems} (got: {scale_b[0].numel()}). Must have "
                    f"swizzle type {expected_swizzle} (got self: {swizzle_a[0]}, mat_b: {swizzle_b[0]})"
                ),
            )
        else:
            torch._check(
                False,
                lambda: (
                    "Invalid scaling configuration. "
                    "For tensorwise scaling, both scales should be scalar. "
                    f"For rowwise scaling, scale_a should be ({M}, 1), scale_b should be (1, {N}). "
                    f"For (BlockWise1x128, BlockWise128x128), scale_a should be ({M}, {ceil_div(K, 128)}), "
                    + f"scale_b should be ({ceil_div(K, 128)}, {ceil_div(N, 128)}). "
                    f"For (BlockWise1x128, BlockWise1x128), scale_a should be ({M}, {ceil_div(K, 128)}), "
                    + f"scale_b should be ({ceil_div(K, 128)}, {N}). "
                    f"Got scale_a.size()=({scale_a[0].size(0)}, {scale_a[0].size(1)}) "
                    f"and scale_b.size()=({scale_b[0].size(0)}, {scale_b[0].size(1)})"
                ),
            )

    _out_dtype = out_dtype if out_dtype is not None else self.dtype
    return torch.empty(M, N, dtype=_out_dtype, device=self.device)