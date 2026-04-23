def __init__(
        self,
        weight_config: dict[str, Any],
        input_config: dict[str, Any],
        moe: FusedMoEConfig,
    ):
        super().__init__(moe)
        self.weight_quant = weight_config
        self.input_quant = input_config

        self.weight_qscheme = self.weight_quant.get("qscheme")
        self.input_qscheme = self.input_quant.get("qscheme")
        self.weight_dtype = self.weight_quant.get("dtype", "").replace(
            "fp8_e4m3", "fp8"
        )
        self.input_dtype = self.input_quant.get("dtype", "").replace("fp8_e4m3", "fp8")
        per_tensor = (
            self.weight_qscheme == "per_tensor" and self.input_qscheme == "per_tensor"
        )
        per_channel = (
            self.weight_qscheme == "per_channel" and self.input_qscheme == "per_channel"
        )
        self.act_quant_group_shape = (
            GroupShape.PER_TOKEN if per_channel else GroupShape.PER_TENSOR
        )
        if not (per_tensor or per_channel):
            raise ValueError(
                "For FP8 Fused MoE layers, only per-tensor and per-channel "
                "scales for weights and activations are supported. Found "
                f"{self.weight_qscheme}, {self.input_qscheme}"
            )  # noqa E501

        self.static_input_scales = not self.input_quant.get("is_dynamic")
        if self.static_input_scales and per_channel:
            raise ValueError(
                "For FP8 Fused MoE layer, we require either per tensor or "
                "channelwise, dynamic per token quantization."
            )

        # For GPUs that lack FP8 hardware support, we can leverage the Marlin
        # kernel for fast weight-only FP8 quantization
        self.use_marlin = (
            not current_platform.has_device_capability(89)
            or envs.VLLM_TEST_FORCE_FP8_MARLIN
        )
        # Disable marlin for rocm
        if current_platform.is_rocm():
            self.use_marlin = False

        self.rocm_aiter_moe_enabled = rocm_aiter_ops.is_fused_moe_enabled()

        self.model_type = getattr(
            get_current_vllm_config().model_config.hf_config, "model_type", None
        )