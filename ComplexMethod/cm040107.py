def quantize(self, mode=None, type_check=True, config=None):
        # Prevent quantization of the subclasses
        if type_check and (type(self) is not EinsumDense):
            raise self._not_implemented_error(self.quantize)

        self.quantization_config = config

        kernel_shape = self._kernel.shape
        if mode in ("int8", "int4", "gptq", "awq"):
            self._set_quantization_info()

        if mode == "int8":
            # Quantize `self._kernel` to int8 and compute corresponding scale
            weight_quantizer = QuantizationConfig.weight_quantizer_or_default(
                self.quantization_config,
                quantizers.AbsMaxQuantizer(axis=self._kernel_reduced_axes),
            )
            kernel_value, kernel_scale = weight_quantizer(
                self._kernel, to_numpy=True
            )
            kernel_scale = self._adjust_scale_for_quant(kernel_scale, "kernel")
            del self._kernel
        elif mode == "int4":
            from keras.src.quantizers.quantization_config import (
                Int4QuantizationConfig,
            )

            block_size = None
            if isinstance(self.quantization_config, Int4QuantizationConfig):
                block_size = self.quantization_config.block_size

            use_grouped = block_size is not None and block_size != -1

            # Flatten kernel to 2D: rows = reduced dims, columns = non-reduced
            rows = 1
            columns = 1
            for i, dim in enumerate(kernel_shape):
                if i in self._kernel_reduced_axes:
                    rows *= dim
                else:
                    columns *= dim

            flat_kernel = ops.reshape(self._kernel, (rows, columns))

            if not use_grouped:
                # Per-channel quantization
                kernel_value_int4, kernel_scale = quantizers.abs_max_quantize(
                    flat_kernel,
                    axis=0,
                    value_range=(-8, 7),
                    dtype="int8",
                    to_numpy=True,
                )
                kernel_scale = ops.squeeze(kernel_scale, axis=0)
            else:
                # Sub-channel quantization with asymmetric zero point
                # Returns kernel [rows, columns], scale [n_groups, columns]
                kernel_value_int4, kernel_scale, kernel_zero = (
                    quantizers.abs_max_quantize_grouped_with_zero_point(
                        flat_kernel, block_size=block_size, to_numpy=True
                    )
                )

            # Pack two int4 values per int8 byte along last axis
            # Stored as [rows, ceil(columns/2)]
            packed_kernel_value, _, _ = quantizers.pack_int4(
                kernel_value_int4, axis=-1
            )
            kernel_value = packed_kernel_value
            del self._kernel
        self.quantized_build(kernel_shape, mode, self.quantization_config)

        # Assign values to the newly created variables.
        if mode in ("int8", "int4"):
            self._kernel.assign(kernel_value)
            self.kernel_scale.assign(kernel_scale)
            # Assign zero point for sub-channel int4 quantization
            if mode == "int4" and use_grouped:
                self.kernel_zero.assign(kernel_zero)

        # Set new dtype policy
        if self.dtype_policy.quantization_mode is None:
            policy_name = mode
            if mode in ("gptq", "awq"):
                policy_name = self.quantization_config.dtype_policy_string()
            elif mode == "int4":
                # Include block_size in policy name for sub-channel quantization
                block_size = get_block_size_for_layer(self, config)
                # Use -1 for per-channel, otherwise use block_size
                block_size_value = -1 if block_size is None else block_size
                policy_name = f"int4/{block_size_value}"
            policy = dtype_policies.get(
                f"{policy_name}_from_{self.dtype_policy.name}"
            )
            self.dtype_policy = policy