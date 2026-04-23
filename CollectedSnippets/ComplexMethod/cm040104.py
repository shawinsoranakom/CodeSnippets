def kernel(self):
        from keras.src.quantizers import gptq_core

        if not self.built:
            raise AttributeError(
                "You must build the layer before accessing `kernel`."
            )

        mode = self.quantization_mode
        is_gptq = mode == "gptq"
        is_awq = mode == "awq"
        is_int4 = mode == "int4"
        gptq_calibrated = bool(getattr(self, "is_gptq_calibrated", False))
        awq_calibrated = bool(getattr(self, "is_awq_calibrated", False))
        gptq_bits = (
            gptq_core.get_weight_bits_for_layer(self, None) if is_gptq else None
        )

        # Decide the source tensor first (packed vs already-quantized vs plain
        # kernel)
        if is_gptq and gptq_calibrated and gptq_bits != 4:
            # calibrated GPTQ, not 4-bit, no unpacking needed
            kernel = self.quantized_kernel
        else:
            # Start with the stored kernel
            kernel = getattr(self, "_kernel", None)

            # Handle int4 unpacking cases in one place
            if is_int4:
                # unpack [rows, ceil(columns/2)] to [rows, columns]
                kernel = quantizers.unpack_int4(
                    kernel,
                    self._int4_unpacked_column_size,
                    axis=-1,
                )
                kernel = ops.reshape(kernel, self.original_kernel_shape)
            elif is_gptq and gptq_calibrated and gptq_bits == 4:
                kernel = quantizers.unpack_int4(
                    self.quantized_kernel,
                    orig_len=self.gptq_unpacked_column_size,
                    axis=0,
                    dtype="uint8",
                )
            elif is_awq and awq_calibrated:
                # AWQ always uses 4-bit quantization
                kernel = quantizers.unpack_int4(
                    self.quantized_kernel,
                    orig_len=self.awq_unpacked_column_size,
                    axis=0,
                    dtype="uint8",
                )

        # Apply LoRA if enabled
        if self.lora_enabled:
            kernel = ops.cast(
                ops.add(
                    kernel,
                    (self.lora_alpha / self.lora_rank)
                    * ops.matmul(self.lora_kernel_a, self.lora_kernel_b),
                ),
                dtype=self.compute_dtype,
            )

        return kernel