def __init__(
        self,
        weight_quant: QuantizationArgs,
        input_quant: QuantizationArgs,
        moe: FusedMoEConfig,
        layer_name: str | None = None,
    ):
        super().__init__(moe)
        self.weight_quant = weight_quant
        self.input_quant = input_quant

        per_tensor = (
            self.weight_quant.strategy == QuantizationStrategy.TENSOR
            and self.input_quant.strategy == QuantizationStrategy.TENSOR
        )
        per_channel = (
            self.weight_quant.strategy == QuantizationStrategy.CHANNEL
            and self.input_quant.strategy == QuantizationStrategy.TOKEN
        )
        if not (per_tensor or per_channel):
            assert self.weight_quant.strategy == QuantizationStrategy.BLOCK
            self.weight_block_size = self.weight_quant.block_structure
            assert self.weight_quant.dynamic is not None
        else:
            self.weight_block_size = None
        self.block_quant = self.weight_block_size is not None

        self.static_input_scales = not self.input_quant.dynamic
        if self.static_input_scales and per_channel:
            raise ValueError(
                "For FP8 Fused MoE layer, we require either per tensor or "
                "channelwise, dynamic per token quantization."
            )

        ct2vllm_weight = {
            QuantizationStrategy.CHANNEL: kFp8StaticChannelSym,
            QuantizationStrategy.TENSOR: kFp8StaticTensorSym,
            QuantizationStrategy.BLOCK: kFp8Static128BlockSym,
        }
        ct2vllm_act = {
            QuantizationStrategy.TOKEN: kFp8DynamicTokenSym,
            QuantizationStrategy.TENSOR: (
                kFp8StaticTensorSym if self.static_input_scales else kFp8Dynamic128Sym
            ),
        }
        weight_key = ct2vllm_weight[self.weight_quant.strategy]
        if weight_key == kFp8Static128BlockSym:
            activation_key = kFp8Dynamic128Sym
        else:
            activation_key = ct2vllm_act[self.input_quant.strategy]

        # Select Fp8 MoE backend
        self.fp8_backend, self.experts_cls = select_fp8_moe_backend(
            config=self.moe,
            weight_key=weight_key,
            activation_key=activation_key,
            allow_vllm_cutlass=True,
        )