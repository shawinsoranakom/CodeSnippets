def _is_fp8_w8a8(
        weight_quant: QuantizationArgs, input_quant: QuantizationArgs
    ) -> bool:
        # Confirm weights and activations quantized.
        if weight_quant is None or input_quant is None:
            return False

        # Confirm weight scheme is supported.
        is_floating_point = (
            weight_quant.type == QuantizationType.FLOAT
            and input_quant.type == QuantizationType.FLOAT
        )
        is_symmetric_weight = weight_quant.symmetric
        is_static_weight = not weight_quant.dynamic
        is_tensor_or_channel_or_block_weight = weight_quant.strategy in [
            QuantizationStrategy.TENSOR,
            QuantizationStrategy.CHANNEL,
            QuantizationStrategy.BLOCK,
        ]
        if not (
            is_floating_point
            and is_symmetric_weight
            and is_static_weight
            and is_tensor_or_channel_or_block_weight
        ):
            return False

        # Dynamic quantization is always supported if weights supported.
        if input_quant.dynamic:
            return True

        # Confirm activation scheme is supported.
        is_symmetric_activation = input_quant.symmetric
        is_per_tensor_activation = input_quant.strategy == QuantizationStrategy.TENSOR
        return is_symmetric_activation and is_per_tensor_activation