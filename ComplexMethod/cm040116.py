def _get_embeddings_with_merged_lora(self):
        """Returns the embeddings with LoRA matrices merged, for serialization.

        This method is called by `save_own_variables` to produce a single
        embeddings tensor that includes the adaptations from LoRA. This is
        useful for deploying the model or for continuing training after
        permanently applying the LoRA update.

        If the layer is quantized (`int8` or `int4`), the process is:
        1. Dequantize the base embeddings to float.
        2. Compute the LoRA delta (`lora_embeddings_a @ lora_embeddings_b`) and
            add it to the dequantized embeddings.
        3. Re-quantize the merged result back to the original quantized
            type (`int8` or packed `int4`), calculating a new scale factor.

        If the layer is not quantized, this method returns the result of the
        `embeddings` property (which computes the merge in floating-point) and a
        scale of `None`.

        If LoRA is not enabled, it returns the original embeddings and scale
        without modification.

        Returns:
            A tuple `(embeddings_value, embeddings_scale, embeddings_zero)`:
                `embeddings_value`: The merged embeddings. A quantized tensor if
                    quantization is active, otherwise a high precision tensor.
                `embeddings_scale`: The quantization scale for the merged
                    embeddings. This is `None` if the layer is not quantized.
                `embeddings_zero`: The zero point for sub-channel quantization.
                    This is `None` for per-channel quantization modes.
        """
        if self.dtype_policy.quantization_mode in (None, "gptq", "awq"):
            return self.embeddings, None, None

        embeddings_value = self._embeddings
        embeddings_scale = self.embeddings_scale
        embeddings_zero = getattr(self, "embeddings_zero", None)

        if not self.lora_enabled:
            return embeddings_value, embeddings_scale, embeddings_zero

        block_size = getattr(self, "_int4_block_size", None)

        # Dequantize embeddings to float.
        if self.quantization_mode == "int4":
            unpacked_embeddings = quantizers.unpack_int4(
                embeddings_value, self._orig_output_dim, axis=-1
            )
            if block_size is None or block_size == -1:
                # Per-channel dequantization
                float_embeddings = ops.divide(
                    ops.cast(unpacked_embeddings, self.compute_dtype),
                    ops.expand_dims(embeddings_scale, axis=-1),
                )
            else:
                # Sub-channel: grouped dequantization using shared utility
                float_embeddings = dequantize_with_sz_map(
                    ops.cast(unpacked_embeddings, self.compute_dtype),
                    embeddings_scale,
                    self.embeddings_zero,
                    self.g_idx,
                    group_axis=-1,
                )
            quant_range = (-8, 7)
        elif self.quantization_mode == "int8":
            float_embeddings = ops.divide(
                ops.cast(embeddings_value, self.compute_dtype),
                ops.expand_dims(embeddings_scale, axis=-1),
            )
            quant_range = (-127, 127)
        else:
            raise ValueError(
                f"Unsupported quantization mode: {self.quantization_mode}"
            )

        # Merge LoRA weights in float domain.
        lora_delta = (self.lora_alpha / self.lora_rank) * ops.matmul(
            self.lora_embeddings_a, self.lora_embeddings_b
        )
        merged_float_embeddings = ops.add(float_embeddings, lora_delta)

        # Requantize.
        if self.quantization_mode == "int4":
            if block_size is None or block_size == -1:
                # Per-channel re-quantization
                requantized_embeddings, new_scale = quantizers.abs_max_quantize(
                    merged_float_embeddings,
                    axis=-1,
                    value_range=quant_range,
                    dtype="int8",
                    to_numpy=True,
                )
                new_scale = ops.squeeze(new_scale, axis=-1)
                embeddings_zero = None
            else:
                # Grouped re-quantization (asymmetric with zero point)
                merged_np = merged_float_embeddings
                # Transpose to (output_dim, input_dim) for grouped quantization
                merged_t = ops.transpose(merged_np)

                requantized_t, scale_t, zero_t = (
                    quantizers.abs_max_quantize_grouped_with_zero_point(
                        merged_t,
                        block_size=block_size,
                        value_range=quant_range,
                        dtype="int8",
                        to_numpy=True,
                    )
                )
                # Transpose back
                requantized_embeddings = ops.transpose(requantized_t)
                new_scale = ops.transpose(scale_t)
                embeddings_zero = ops.transpose(zero_t)

            # Pack for int4
            embeddings_value, _, _ = quantizers.pack_int4(
                requantized_embeddings, axis=-1
            )
            embeddings_scale = new_scale
        else:
            # int8 re-quantization
            requantized_embeddings, embeddings_scale = (
                quantizers.abs_max_quantize(
                    merged_float_embeddings,
                    axis=-1,
                    value_range=quant_range,
                    dtype="int8",
                    to_numpy=True,
                )
            )
            embeddings_scale = ops.squeeze(embeddings_scale, axis=-1)
            embeddings_value = requantized_embeddings
            embeddings_zero = None
        return embeddings_value, embeddings_scale, embeddings_zero