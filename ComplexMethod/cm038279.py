def can_implement(cls, c: MPLinearLayerConfig) -> tuple[bool, str | None]:
        if not current_platform.is_cpu():
            return False, "Only CPU is supported"
        if c.weight_type not in cls.SUPPORTED_QUANT_TYPES:
            return False, f"Unsupported quant type {c.weight_type}"
        if (
            current_platform.get_cpu_architecture() == CpuArchEnum.ARM
            and c.act_type
            not in [
                torch.float32,
                torch.bfloat16,
                torch.float16,
            ]
        ):
            return (
                False,
                "Dynamic4bitLinearKernel on Arm requires Float32 or"
                " BFloat16 or Float16 activations",
            )
        if c.full_weight_shape[0] % c.group_size != 0:
            return (
                False,
                f"Group size ({c.group_size}) does not evenly divide"
                " the number of input features "
                f"({c.full_weight_shape[0]})",
            )
        if current_platform.get_cpu_architecture() == CpuArchEnum.ARM:
            try:
                # Attempt to retrieve the operation
                _ = torch.ops.aten._dyn_quant_matmul_4bit
            except AttributeError:
                return (
                    False,
                    f"PyTorch {torch.__version__} does not support"
                    " _dyn_quant_matmul_4bit. Install a newer version",
                )
        return True, None