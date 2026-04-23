def can_implement(cls, c: MPLinearLayerConfig) -> tuple[bool, str | None]:
        if not current_platform.is_xpu():
            return False, "XPUwNa16 only supported on XPU"

        if c.act_type != torch.bfloat16 and c.act_type != torch.float16:
            return False, "XPUwNa16 only supports BF16/FP16 activations"

        if c.weight_type not in _XPUWNA16_SUPPORTED_QUANT_TYPES:
            return (
                False,
                f"Quant type ({c.weight_type}) not supported by "
                "XPUwNa16, supported types are: "
                f"{_XPUWNA16_SUPPORTED_QUANT_TYPES}",
            )
        if c.group_size != -1 and c.group_size % 32 != 0:
            return (
                False,
                f"Group size ({c.group_size}) not supported by "
                "XPUwNa16, supported group sizes are multiples of 32",
            )

        if c.partition_weight_shape[0] % 32 != 0:
            return (
                False,
                f"Input size ({c.partition_weight_shape[0]}) not supported by "
                "XPUwNa16, supported sizes are multiples of 32",
            )

        if c.partition_weight_shape[1] % 32 != 0:
            return (
                False,
                f"Output size ({c.partition_weight_shape[1]}) not supported by "
                "XPUWNA16, supported sizes are multiples of 32",
            )

        return True, None