def quantize(self, mode=None, type_check=True, config=None):
        # Prevent quantization of the subclasses.
        if type_check and (type(self) is not Embedding):
            raise self._not_implemented_error(self.quantize)

        self.quantization_config = config

        embeddings_shape = (self.input_dim, self.output_dim)
        if mode == "int8":
            # Quantize `self._embeddings` to int8 and compute corresponding
            # scale.
            weight_quantizer = QuantizationConfig.weight_quantizer_or_default(
                self.quantization_config,
                quantizers.AbsMaxQuantizer(axis=-1),
            )
            embeddings_value, embeddings_scale = weight_quantizer(
                self._embeddings, to_numpy=True
            )
            embeddings_scale = ops.squeeze(embeddings_scale, axis=-1)
            del self._embeddings
            self.quantized_build(
                embeddings_shape, mode, self.quantization_config
            )
            self._embeddings.assign(embeddings_value)
            self.embeddings_scale.assign(embeddings_scale)
        elif mode == "int4":
            from keras.src.quantizers.quantization_config import (
                Int4QuantizationConfig,
            )

            block_size = None
            if isinstance(self.quantization_config, Int4QuantizationConfig):
                block_size = self.quantization_config.block_size

            use_grouped = block_size is not None and block_size != -1

            if not use_grouped:
                # Per-channel quantization
                weight_quantizer = (
                    QuantizationConfig.weight_quantizer_or_default(
                        self.quantization_config,
                        quantizers.AbsMaxQuantizer(
                            axis=-1,
                            value_range=(-8, 7),
                            output_dtype="int8",
                        ),
                    )
                )
                embeddings_value, embeddings_scale = weight_quantizer(
                    self._embeddings, to_numpy=True
                )
                embeddings_scale = ops.squeeze(embeddings_scale, axis=-1)
            else:
                # Sub-channel quantization with asymmetric zero point
                input_dim, output_dim = ops.shape(self._embeddings)
                # Transpose to put output_dim first for grouped quantization
                embeddings_t = ops.transpose(self._embeddings)

                embeddings_value_t, scale_t, zero_t = (
                    quantizers.abs_max_quantize_grouped_with_zero_point(
                        embeddings_t,
                        block_size=block_size,
                        value_range=(-8, 7),
                        dtype="int8",
                        to_numpy=True,
                    )
                )
                # Transpose back to (input_dim, output_dim) layout
                embeddings_value = ops.transpose(embeddings_value_t)
                embeddings_scale = ops.transpose(scale_t)
                embeddings_zero = ops.transpose(zero_t)

            packed_embeddings_value, _, _ = quantizers.pack_int4(
                embeddings_value, axis=-1
            )
            del self._embeddings
            self.quantized_build(
                embeddings_shape, mode, self.quantization_config
            )
            self._embeddings.assign(packed_embeddings_value)
            self.embeddings_scale.assign(embeddings_scale)
            if use_grouped:
                self.embeddings_zero.assign(embeddings_zero)
        else:
            raise self._quantization_mode_error(mode)

        # Set new dtype policy.
        if self.dtype_policy.quantization_mode is None:
            policy_name = mode
            if mode == "int4":
                # Include block_size in policy name for sub-channel quantization
                block_size = get_block_size_for_layer(self, config)
                block_size_value = -1 if block_size is None else block_size
                policy_name = f"int4/{block_size_value}"
            policy = dtype_policies.get(
                f"{policy_name}_from_{self.dtype_policy.name}"
            )
            self.dtype_policy = policy