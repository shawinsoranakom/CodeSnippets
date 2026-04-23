def _infer_scale_swizzle_impl(
    mat_size: tuple[Any, Any],
    scale_size: tuple[Any, ...],
    scale_numel: Any,
    mat_dtype: torch.dtype,
    scale_dtype: torch.dtype,
    eq_fn: Callable[[Any, Any], bool],
) -> tuple[Any | None, Any | None]:
    """
    Core implementation for scale/swizzle inference.
    """
    from torch.nn.functional import ScalingType, SwizzleType

    # Tensor-wise: single scale for entire tensor
    if eq_fn(scale_numel, 1):
        return ScalingType.TensorWise, SwizzleType.NO_SWIZZLE

    # Row-wise: one scale per row or column
    if len(scale_size) >= 2:
        if (eq_fn(scale_size[0], mat_size[0]) and eq_fn(scale_size[1], 1)) or (
            eq_fn(scale_size[0], 1) and eq_fn(scale_size[1], mat_size[1])
        ):
            return ScalingType.RowWise, SwizzleType.NO_SWIZZLE

        # Block-wise 1x128 / 128x1 (DeepGemm style)
        if (
            eq_fn(scale_size[0], mat_size[0])
            and eq_fn(scale_size[1], ceildiv(mat_size[1], 128))
        ) or (
            eq_fn(scale_size[1], mat_size[1])
            and eq_fn(scale_size[0], ceildiv(mat_size[0], 128))
        ):
            return ScalingType.BlockWise1x128, SwizzleType.NO_SWIZZLE

        # Block-wise 128x128
        if eq_fn(scale_size[0], ceildiv(mat_size[0], 128)) and eq_fn(
            scale_size[1], ceildiv(mat_size[1], 128)
        ):
            return ScalingType.BlockWise128x128, SwizzleType.NO_SWIZZLE

    # Adjust for packed FP4 data (2 values per element)
    K_multiplier = 2 if mat_dtype == torch.float4_e2m1fn_x2 else 1

    # NVFP4: BlockWise1x16 with float8_e4m3fn scales
    if mat_dtype == torch.float4_e2m1fn_x2 and scale_dtype == torch.float8_e4m3fn:
        expected_numel_a = _round_up(mat_size[0], 128) * _round_up(
            ceildiv(K_multiplier * mat_size[1], 16), 4
        )
        expected_numel_b = _round_up(mat_size[1], 128) * _round_up(
            ceildiv(K_multiplier * mat_size[0], 16), 4
        )
        if eq_fn(scale_numel, expected_numel_a) or eq_fn(scale_numel, expected_numel_b):
            return ScalingType.BlockWise1x16, SwizzleType.SWIZZLE_32_4_4

    # MXFP8: BlockWise1x32 with float8_e8m0fnu scales
    if scale_dtype == torch.float8_e8m0fnu:
        if not torch.version.hip:
            # NVIDIA: uses swizzled 32x4x4 layout
            expected_numel_a = _round_up(mat_size[0], 128) * _round_up(
                ceildiv(K_multiplier * mat_size[1], 32), 4
            )
            expected_numel_b = _round_up(mat_size[1], 128) * _round_up(
                ceildiv(K_multiplier * mat_size[0], 32), 4
            )
            if eq_fn(scale_numel, expected_numel_a) or eq_fn(
                scale_numel, expected_numel_b
            ):
                return ScalingType.BlockWise1x32, SwizzleType.SWIZZLE_32_4_4
        else:
            # AMD: no swizzle
            expected_numel_a = ceildiv(mat_size[0], 32) * K_multiplier * mat_size[1]
            expected_numel_b = ceildiv(K_multiplier * mat_size[1], 32) * mat_size[0]
            if eq_fn(scale_numel, expected_numel_a) or eq_fn(
                scale_numel, expected_numel_b
            ):
                return ScalingType.BlockWise1x32, SwizzleType.NO_SWIZZLE

    return None, None