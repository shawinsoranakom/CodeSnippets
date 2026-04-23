def _get_kernel_with_merged_lora(self):
        """Returns the kernel with LoRA matrices merged, for serialization.

        This method is called by `save_own_variables` to produce a single
        kernel tensor that includes the adaptations from LoRA. This is useful
        for deploying the model or for continuing training after permanently
        applying the LoRA update.

        If the layer is quantized (`int8` or `int4`), the process is:
        1. Dequantize the base kernel to float.
        2. Compute the LoRA delta (`lora_kernel_a @ lora_kernel_b`) and add
            it to the dequantized kernel.
        3. Re-quantize the merged result back to the original quantized
            type (`int8` or packed `int4`), calculating a new scale factor.

        If the layer is not quantized, this method returns the result of the
        `kernel` property (which computes the merge in floating-point) and a
        scale of `None`.

        If LoRA is not enabled, it returns the original kernel and scale
        without modification.

        Returns:
            A tuple `(kernel_value, kernel_scale, kernel_zero)`:
                `kernel_value`: The merged kernel. A quantized tensor if
                    quantization is active, otherwise a high precision tensor.
                `kernel_scale`: The quantization scale for the merged kernel.
                    This is `None` if the layer is not quantized.
                `kernel_zero`: The zero point for sub-channel int4 quantization.
                    This is `None` for per-channel or non-int4 modes.
        """
        if self.dtype_policy.quantization_mode in (None, "gptq", "awq"):
            return self.kernel, None, None

        kernel_value = self._kernel
        kernel_scale = self.kernel_scale
        kernel_zero = getattr(self, "kernel_zero", None)

        if not self.lora_enabled:
            return kernel_value, kernel_scale, kernel_zero

        # Dequantize, Merge, and Re-quantize
        block_size = getattr(self, "_int4_block_size", None)

        # Step 1: Dequantize kernel to float
        if self.quantization_mode == "int4":
            # Unpack along last axis ([in, out])
            unpacked_kernel = quantizers.unpack_int4(
                kernel_value, self._orig_output_dim, axis=-1
            )
            if block_size is None or block_size == -1:
                # Per-channel: kernel [in, out], scale [out]
                float_kernel = ops.divide(
                    ops.cast(unpacked_kernel, self.compute_dtype),
                    kernel_scale,
                )
            else:
                # Sub-channel: scale/zero are [n_groups, out]
                float_kernel = dequantize_with_sz_map(
                    unpacked_kernel,
                    kernel_scale,
                    self.kernel_zero,
                    self.g_idx,
                    group_axis=0,
                )
                float_kernel = ops.cast(float_kernel, self.compute_dtype)
            quant_range = (-8, 7)
        elif self.quantization_mode == "int8":
            float_kernel = ops.divide(
                ops.cast(kernel_value, self.compute_dtype), kernel_scale
            )
            quant_range = (-127, 127)
        else:
            raise ValueError(
                f"Unsupported quantization mode: {self.quantization_mode}"
            )

        # Step 2: Merge LoRA weights in float domain
        lora_delta = (self.lora_alpha / self.lora_rank) * ops.matmul(
            self.lora_kernel_a, self.lora_kernel_b
        )
        merged_float_kernel = ops.add(float_kernel, lora_delta)

        # Step 3: Re-quantize the merged kernel
        if (
            self.quantization_mode == "int4"
            and block_size is not None
            and block_size != -1
        ):
            # Sub-channel: returns kernel [in, out], scale [n_groups, out]
            requantized_kernel, kernel_scale, kernel_zero = (
                quantizers.abs_max_quantize_grouped_with_zero_point(
                    merged_float_kernel, block_size=block_size, to_numpy=True
                )
            )
        elif self.quantization_mode == "int4":
            # Per-channel: quantize along input axis (axis=0)
            requantized_kernel, kernel_scale = quantizers.abs_max_quantize(
                merged_float_kernel,
                axis=0,
                value_range=quant_range,
                dtype="int8",
                to_numpy=True,
            )
            kernel_scale = ops.squeeze(kernel_scale, axis=0)
            kernel_zero = None
        else:
            requantized_kernel, kernel_scale = quantizers.abs_max_quantize(
                merged_float_kernel,
                axis=0,
                value_range=quant_range,
                dtype="int8",
                to_numpy=True,
            )
            kernel_scale = ops.squeeze(kernel_scale, axis=0)
            kernel_zero = None

        if self.quantization_mode == "int4":
            # Pack along last axis
            kernel_value, _, _ = quantizers.pack_int4(
                requantized_kernel, axis=-1
            )
        else:
            kernel_value = requantized_kernel
        return kernel_value, kernel_scale, kernel_zero