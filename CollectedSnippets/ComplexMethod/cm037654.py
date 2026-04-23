def __init__(
        self,
        weight_quant: QuantizationArgs,
        input_quant: QuantizationArgs,
        moe: FusedMoEConfig,
        layer_name: str | None = None,
    ):
        super().__init__(moe)
        self.has_bias = self.moe.has_bias
        self.weight_quant = weight_quant
        self.input_quant = input_quant

        # Validate scheme: weights=W4 (channel or group),
        # activations=dynamic TOKEN (A8)

        # Must be dynamic per-token activations
        if (
            input_quant.strategy != QuantizationStrategy.TOKEN
            or not input_quant.dynamic
        ):
            raise ValueError(
                "W4A8-int MoE needs dynamic per-token activation quantization."
            )

        # Weight can be channel-wise (group_size=None) or group-wise
        self.group_size = (
            weight_quant.group_size if (weight_quant.group_size is not None) else -1
        )
        if weight_quant.num_bits != 4:
            raise ValueError("This method only supports 4-bit weights (num_bits=4).")

        # CPU only
        if not current_platform.is_cpu():
            raise ValueError("CompressedTensorsW4A8Int8MoEMethod is CPU-only.")

        # Arm: check _dyn ops availability
        if current_platform.get_cpu_architecture() == CpuArchEnum.ARM:
            try:
                _ = torch.ops.aten._dyn_quant_matmul_4bit
                _ = torch.ops.aten._dyn_quant_pack_4bit_weight
            except AttributeError as err:
                raise RuntimeError(
                    f"""PyTorch {torch.__version__} lacks _dyn_quant_* 4bit ops;
                    install a newer build."""
                ) from err
        self.static_input_scales = False