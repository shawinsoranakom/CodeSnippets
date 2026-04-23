def __init__(
        self,
        quant_key: QuantKey,
        enabled: bool | None = None,
        has_col_major_scales: bool = False,
        is_e8m0: bool = False,
        match_rocm_aiter: bool = False,
        is_tma_aligned: bool = False,
    ) -> None:
        if enabled is None:
            enabled = QuantFP8.enabled()

        super().__init__(enabled)
        self.quant_key = quant_key
        self.has_col_major_scales = has_col_major_scales
        self.is_e8m0 = is_e8m0
        self.match_rocm_aiter = match_rocm_aiter
        self.is_tma_aligned = is_tma_aligned

        if match_rocm_aiter:
            assert not quant_key.scale.group_shape.is_per_tensor(), (
                "ROCm aiter fusion pass does not support per tensor quantization"
            )
            if quant_key.scale.group_shape.is_per_token():
                self.QUANT_OP = rocm_aiter_ops.get_per_token_quant_op()
            else:
                assert quant_key.scale.group_shape.col == 128, (
                    "ROCm aiter fusion pass currently supports "
                    "quantization operation with group_size 128"
                )
                if current_platform.is_fp8_fnuz():
                    self.QUANT_OP = rocm_aiter_ops.get_group_quant_op()
                else:
                    self.QUANT_OP = (
                        torch.ops.vllm.triton_per_token_group_quant_fp8.default
                    )

        else:
            assert quant_key in QUANT_OPS, (
                f"unsupported quantization scheme {quant_key}"
            )
            self.QUANT_OP = QUANT_OPS[quant_key]

            assert quant_key.dtype == current_platform.fp8_dtype(), (
                "Only QuantFP8 supported by"
            )
            assert quant_key.scale2 is None

        self.quant_fp8 = QuantFP8(
            quant_key.scale.static,
            quant_key.scale.group_shape,
            column_major_scales=has_col_major_scales,
            use_ue8m0=is_e8m0,
            tma_aligned_scales=self.is_tma_aligned,
            compile_native=False,
        )