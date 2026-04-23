def _get_kernel_with_merged_lora(self):
        """Returns the kernel with LoRA matrices merged, for serialization.

        This method is called by `save_own_variables` to produce a single
        kernel tensor that includes the adaptations from LoRA. This is useful
        for deploying the model or for continuing training after permanently
        applying the LoRA update.

        If the layer is quantized (`int8` or `int4`), the process is:
        1. Dequantize the base kernel to float.
        2. Adjust the scale tensor layout for dequantization. This is the
            reverse order of operations used when building the layer.
        3. Compute the LoRA delta (`lora_kernel_a @ lora_kernel_b`) and add
            it to the dequantized kernel.
        4. Re-quantize the merged result back to the original quantized
            type (`int8` or packed `int4`), calculating a new scale factor.
        5. Adjust the scale tensor layout for quantization. This is the forward
            order of operations used when building the layer.

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
        # If not a quantized layer, return the full-precision kernel directly.
        if self.dtype_policy.quantization_mode in (None, "gptq", "awq"):
            return self.kernel, None, None

        kernel_zero = getattr(self, "kernel_zero", None)

        # If quantized but LoRA is not enabled, return the original quantized
        # kernel.
        if not self.lora_enabled:
            return self._kernel, self.kernel_scale, kernel_zero

        # Dequantize, Merge, and Re-quantize

        # 1. Dequantize the kernel
        if self.quantization_mode == "int4":
            # Unpack [rows, ceil(columns/2)] to [rows, columns]
            unpacked_kernel = quantizers.unpack_int4(
                self._kernel,
                self._int4_unpacked_column_size,
                axis=-1,
            )
            block_size = getattr(self, "_int4_block_size", None)
            if block_size is not None and block_size != -1:
                # Grouped dequantization with group_axis=0
                kernel_fp = dequantize_with_sz_map(
                    unpacked_kernel,
                    self.kernel_scale,
                    self.kernel_zero,
                    self.g_idx,
                    group_axis=0,
                )
            else:
                # Per-channel dequantization:
                # kernel [rows, columns], scale [columns]
                kernel_fp = ops.divide(
                    ops.cast(unpacked_kernel, self.compute_dtype),
                    self.kernel_scale,
                )
            kernel_fp = ops.reshape(kernel_fp, self.original_kernel_shape)
        elif self.quantization_mode == "int8":
            adjusted_scale = self._adjust_scale_for_dequant(self.kernel_scale)
            kernel_fp = ops.divide(self._kernel, adjusted_scale)
        else:
            raise ValueError(
                f"Unsupported quantization mode: {self.quantization_mode}"
            )

        # 2. Merge the LoRA update in the float domain
        lora_update = (self.lora_alpha / self.lora_rank) * ops.matmul(
            self.lora_kernel_a, self.lora_kernel_b
        )
        merged_kernel = ops.add(kernel_fp, lora_update)

        # 3. Re-quantize the merged float kernel back to the target format
        if self.quantization_mode == "int4":
            block_size = getattr(self, "_int4_block_size", None)
            rows = self._int4_rows
            columns = self._int4_unpacked_column_size

            # Flatten to 2D [rows, columns]
            flat_kernel = ops.reshape(merged_kernel, (rows, columns))

            if block_size is not None and block_size != -1:
                # Use abs_max_quantize_grouped_with_zero_point for proper
                # signed quantization (same as quantize() method)
                # Returns kernel [rows, columns], scale [n_groups, columns]
                kernel_quant, new_scale, new_zero = (
                    quantizers.abs_max_quantize_grouped_with_zero_point(
                        flat_kernel, block_size=block_size, to_numpy=True
                    )
                )
                kernel_zero = new_zero
            else:
                # Per-channel: quantize along rows axis
                kernel_quant, new_scale = quantizers.abs_max_quantize(
                    flat_kernel,
                    axis=0,
                    value_range=(-8, 7),
                    dtype="int8",
                    to_numpy=True,
                )
                new_scale = ops.squeeze(new_scale, axis=0)
                kernel_zero = None

            # Pack along last axis
            new_kernel, _, _ = quantizers.pack_int4(kernel_quant, axis=-1)
        elif self.quantization_mode == "int8":
            new_kernel, new_scale = quantizers.abs_max_quantize(
                merged_kernel,
                axis=self._kernel_reduced_axes,
                to_numpy=True,
            )
            new_scale = self._adjust_scale_for_quant(new_scale, "kernel")
            kernel_zero = None

        return new_kernel, new_scale, kernel_zero