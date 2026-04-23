def supports_cutlass_24(
        weight_quant: QuantizationArgs | None,
        input_quant: QuantizationArgs | None,
        sparsity_scheme: SparsityCompressionConfig | None = None,
    ) -> bool:
        """
        Check if the layer is supported by the Cutlass 2:4 Kernel
        Conditions:
            - Overarching condition: Sparsity Structure is 2:4
            - Unquantized cases are supported
            - Weight only quantization is not-supported
            - Supported weight quantization strategies are TENSOR and CHANNEL
            - Supported input quantization strategies are TENSOR and TOKEN
            - Only 8 bit quantization is supported

        :return: True if the layer is supported by the Cutlass 2:4 Kernel
            False otherwise
        """
        if sparsity_scheme is None:
            return False

        is_valid_sparsity_structure: bool = (
            sparsity_scheme.sparsity_structure == SparsityStructure.TWO_FOUR.value
        )

        valid_compressors = {
            CompressionFormat.dense.value,
            CompressionFormat.sparse_24_bitmask.value,
        }

        is_valid_sparsity = (
            is_valid_sparsity_structure and sparsity_scheme.format in valid_compressors
        )

        if not is_valid_sparsity:
            return False

        # Unquantized cases are supported
        if weight_quant is None and input_quant is None:
            return True

        # Weight only quantization is not-supported
        if weight_quant is not None and input_quant is None:
            return False

        supported_weight_quant_strategies = [
            QuantizationStrategy.TENSOR.value,
            QuantizationStrategy.CHANNEL.value,
        ]

        assert weight_quant is not None
        assert input_quant is not None
        if weight_quant.strategy not in supported_weight_quant_strategies:
            return False

        supported_input_quant_strategies = [
            QuantizationStrategy.TENSOR.value,
            QuantizationStrategy.TOKEN.value,
        ]

        if input_quant.strategy not in supported_input_quant_strategies:
            return False

        return weight_quant.num_bits == input_quant.num_bits == 8