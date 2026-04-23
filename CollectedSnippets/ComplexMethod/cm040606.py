def __init__(
        self,
        weight_quantizer=None,
        activation_quantizer="default",
        block_size=128,
    ):
        if activation_quantizer == "default":
            # Use weight-only quantization by default for int4
            activation_quantizer = None
        super().__init__(weight_quantizer, activation_quantizer)

        # Validate block_size
        if block_size is not None and block_size != -1 and block_size <= 0:
            raise ValueError(
                f"block_size must be None, -1, or a positive integer. "
                f"Received: block_size={block_size}"
            )
        self.block_size = block_size

        # Sub-channel quantization does not support custom quantizers
        is_sub_channel = block_size is not None and block_size > 0
        has_custom_quantizer = (
            self.weight_quantizer is not None
            or self.activation_quantizer is not None
        )
        if is_sub_channel and has_custom_quantizer:
            raise ValueError(
                "Int4 sub-channel quantization (block_size > 0) does not "
                "support custom quantizers. Either set block_size to None "
                "or -1 for per-channel quantization, or remove the custom "
                f"quantizer arguments. Received: block_size={block_size}"
            )

        if self.weight_quantizer is not None:
            if self.weight_quantizer.value_range != (-8, 7):
                raise ValueError(
                    "Int4QuantizationConfig requires a weight_quantizer "
                    "with value_range=(-8, 7). Received: "
                    f"value_range={self.weight_quantizer.value_range}"
                )

            if self.weight_quantizer.output_dtype != "int8":
                raise ValueError(
                    "Int4QuantizationConfig requires a weight_quantizer "
                    "with output_dtype='int8'. Received: "
                    f"output_dtype={self.weight_quantizer.output_dtype}"
                )