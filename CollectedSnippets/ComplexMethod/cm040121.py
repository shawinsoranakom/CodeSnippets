def quantize(self, mode=None, type_check=True, config=None):
        # Prevent quantization of the subclasses
        if type_check and (type(self) is not Dense):
            raise self._not_implemented_error(self.quantize)

        self.quantization_config = config

        kernel_shape = self._kernel.shape
        if mode == "int8":
            weight_quantizer = QuantizationConfig.weight_quantizer_or_default(
                self.quantization_config, quantizers.AbsMaxQuantizer(axis=0)
            )
            kernel_value, kernel_scale = weight_quantizer(
                self._kernel, to_numpy=True
            )
            kernel_scale = ops.squeeze(kernel_scale, axis=0)
            del self._kernel
            # Build variables for int8 mode
            self.quantized_build(kernel_shape, mode, self.quantization_config)
            self._kernel.assign(kernel_value)
            self.kernel_scale.assign(kernel_scale)
        elif mode == "int4":
            from keras.src.quantizers.quantization_config import (
                Int4QuantizationConfig,
            )

            block_size = None
            if isinstance(self.quantization_config, Int4QuantizationConfig):
                block_size = self.quantization_config.block_size

            if block_size is None or block_size == -1:
                # Per-channel quantization
                weight_quantizer = (
                    QuantizationConfig.weight_quantizer_or_default(
                        self.quantization_config,
                        quantizers.AbsMaxQuantizer(
                            axis=0, value_range=(-8, 7), output_dtype="int8"
                        ),
                    )
                )
                kernel_value_int4, kernel_scale = weight_quantizer(
                    self._kernel, to_numpy=True
                )
                kernel_scale = ops.squeeze(kernel_scale, axis=0)
            else:
                # Sub-channel quantization with asymmetric zero point
                # Returns kernel [in, out], scale [n_groups, out], zero
                # [n_groups, out]
                kernel_value_int4, kernel_scale, kernel_zero = (
                    quantizers.abs_max_quantize_grouped_with_zero_point(
                        self._kernel, block_size=block_size, to_numpy=True
                    )
                )

            # Pack two int4 values per int8 byte along last axis
            # Stored as [in, ceil(out/2)]
            packed_kernel_value, _, _ = quantizers.pack_int4(
                kernel_value_int4, axis=-1
            )
            del self._kernel
            self.quantized_build(kernel_shape, mode, self.quantization_config)
            self._kernel.assign(packed_kernel_value)
            self.kernel_scale.assign(kernel_scale)
            if block_size is not None and block_size > 0:
                self.kernel_zero.assign(kernel_zero)
        elif mode == "gptq":
            self.quantized_build(kernel_shape, mode, self.quantization_config)
        elif mode == "awq":
            self.quantized_build(kernel_shape, mode, self.quantization_config)
        elif mode == "float8":
            self.quantized_build(kernel_shape, mode)
        else:
            raise self._quantization_mode_error(mode)

        # Set new dtype policy only for modes that already have a policy.
        if self.dtype_policy.quantization_mode is None:
            from keras.src import dtype_policies  # local import to avoid cycle

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