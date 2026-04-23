def can_implement(cls, c: MPLinearLayerConfig) -> tuple[bool, str | None]:
        if not current_platform.is_cuda():
            return False, "CUTLASS only supported on CUDA"

        if not current_platform.is_device_capability(90):
            return False, "CUTLASS W4A8 requires compute capability of 90 (Hopper)"

        if c.act_type != torch.float8_e4m3fn:
            return False, "CUTLASS W4A8 only supports FP8 (e4m3) activations"

        if c.has_g_idx:
            return False, "Act reordering not supported by CUTLASS W4A8"

        if c.zero_points:
            return False, "Zero points not supported by CUTLASS W4A8"

        if c.weight_type != scalar_types.int4:
            return (
                False,
                f"Quant type ({c.weight_type}) not supported by "
                "CUTLASS W4A8, only supported int4",
            )

        if c.group_size != 128:
            return False, "Only group_size 128 is supported"

        in_features, out_features = c.partition_weight_shape
        if in_features % 128 or out_features % 128:
            return (
                False,
                f"K and N must be divisible by 128, got {c.partition_weight_shape}",
            )

        if c.out_type != torch.bfloat16:
            return (
                False,
                f"Only bfloat16 output type currently supportedgot {c.out_type=}",
            )

        return True, None