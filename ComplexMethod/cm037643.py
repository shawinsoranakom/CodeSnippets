def _get_scheme_from_parts(
        self,
        weight_quant: QuantizationArgs,
        input_quant: QuantizationArgs,
        format: str | None = None,
        layer_name: str | None = None,
    ) -> "CompressedTensorsScheme":
        # use the per-layer format if defined, otherwise, use global format
        format = format if format is not None else self.quant_format

        # Detect If Mixed Precision
        if self._is_nvfp4_format(weight_quant) and input_quant is None:
            return CompressedTensorsW4A16Fp4()

        if self._is_mxfp4(weight_quant):
            return CompressedTensorsW4A16Mxfp4()

        if self._is_mxfp8(weight_quant):
            return CompressedTensorsW8A8Mxfp8()

        if self._is_fp8_w4a8_sm90(weight_quant, input_quant):
            return CompressedTensorsW4A8Fp8(
                num_bits=weight_quant.num_bits,
                strategy=weight_quant.strategy,
                symmetric=weight_quant.symmetric,
                group_size=weight_quant.group_size,
                actorder=weight_quant.actorder,
            )

        if (
            self._is_wNa16_group_channel(weight_quant, input_quant)
            and (format == CompressionFormat.pack_quantized.value)
            and (weight_quant.num_bits in WNA16_SUPPORTED_BITS)
        ):
            return CompressedTensorsWNA16(
                num_bits=weight_quant.num_bits,
                strategy=weight_quant.strategy,
                symmetric=weight_quant.symmetric,
                group_size=weight_quant.group_size,
                actorder=weight_quant.actorder,
                layer_name=layer_name,
            )

        act_quant_format = is_activation_quantization_format(format)
        if act_quant_format:
            if self._is_nvfp4_format(weight_quant) and self._is_nvfp4_format(
                input_quant
            ):
                return CompressedTensorsW4A4Fp4()

            if self._is_fp8_w8a8(weight_quant, input_quant):
                is_fp8_w8a8_supported = self._check_scheme_supported(
                    CompressedTensorsW8A8Fp8.get_min_capability(), error=False
                )
                if is_fp8_w8a8_supported:
                    return CompressedTensorsW8A8Fp8(
                        weight_quant=weight_quant,
                        is_static_input_scheme=(
                            input_quant and not input_quant.dynamic
                        ),
                    )
                else:
                    # note: input_quant will be present for converted models;
                    # will be ignored during inference post loading
                    return CompressedTensorsW8A16Fp8(
                        weight_quant=weight_quant,
                        is_static_input_scheme=not input_quant.dynamic,
                    )

            # note: input_quant can be None
            if self._is_fp8_w8a16(weight_quant, input_quant):
                is_static_input_scheme = input_quant and not input_quant.dynamic
                return CompressedTensorsW8A16Fp8(
                    weight_quant=weight_quant,
                    is_static_input_scheme=is_static_input_scheme,
                )

            if self._is_static_tensor_w8a8(weight_quant, input_quant):
                return CompressedTensorsW8A8Int8(
                    strategy=weight_quant.strategy,
                    is_static_input_scheme=True,
                    input_symmetric=input_quant.symmetric,
                )

            if self._is_dynamic_token_w8a8(weight_quant, input_quant):
                return CompressedTensorsW8A8Int8(
                    strategy=weight_quant.strategy,
                    is_static_input_scheme=False,
                    input_symmetric=input_quant.symmetric,
                )

            if self._is_dynamic_token_w4a8_int(weight_quant, input_quant):
                is_static_input_scheme = input_quant and not input_quant.dynamic
                return CompressedTensorsW4A8Int(
                    num_bits=weight_quant.num_bits,
                    strategy=weight_quant.strategy,
                    group_size=weight_quant.group_size,
                    is_static_input_scheme=is_static_input_scheme,
                    input_symmetric=input_quant.symmetric,
                )

        raise NotImplementedError("No compressed-tensors compatible scheme was found.")