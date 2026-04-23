def save_own_variables(self, store):
        # Do nothing if the layer isn't yet built
        if not self.built:
            return
        mode = self.quantization_mode
        if mode not in self.variable_serialization_spec:
            raise self._quantization_mode_error(mode)

        # Kernel plus optional merged LoRA-aware scale/zero (returns
        # (kernel, None, None) for None/gptq/awq)
        kernel_value, merged_kernel_scale, merged_kernel_zero = (
            self._get_kernel_with_merged_lora()
        )
        idx = 0
        for name in self.variable_serialization_spec[mode]:
            if name == "kernel":
                store[str(idx)] = kernel_value
            elif name == "bias" and self.bias is None:
                continue
            elif name == "kernel_zero":
                if merged_kernel_zero is None:
                    # kernel_zero only exists for sub-channel int4 quantization
                    continue
                store[str(idx)] = merged_kernel_zero
            elif name == "g_idx":
                if not hasattr(self, "g_idx"):
                    # g_idx only exists for sub-channel int4 quantization
                    continue
                store[str(idx)] = self.g_idx
            elif name == "kernel_scale" and mode in ("int4", "int8"):
                # For int4/int8, the merged LoRA scale (if any) comes from
                # `_get_kernel_with_merged_lora()`
                store[str(idx)] = merged_kernel_scale
            else:
                store[str(idx)] = getattr(self, name)
            idx += 1