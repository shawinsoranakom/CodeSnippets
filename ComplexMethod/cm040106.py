def load_own_variables(self, store):
        if not self.lora_enabled:
            self._check_load_own_variables(store)
        # Do nothing if the layer isn't yet built
        if not self.built:
            return
        mode = self.quantization_mode
        if mode not in self.variable_serialization_spec:
            raise self._quantization_mode_error(mode)

        # A saved GPTQ/AWQ quantized model will always be calibrated.
        self.is_gptq_calibrated = mode == "gptq"
        self.is_awq_calibrated = mode == "awq"

        idx = 0
        for name in self.variable_serialization_spec[mode]:
            if name == "kernel":
                self._kernel.assign(store[str(idx)])
            elif name == "bias" and self.bias is None:
                continue
            elif name == "kernel_zero" and not hasattr(self, "kernel_zero"):
                # kernel_zero only exists for sub-channel int4 quantization
                continue
            elif name == "g_idx" and not hasattr(self, "g_idx"):
                # g_idx only exists for sub-channel int4 quantization
                continue
            else:
                getattr(self, name).assign(store[str(idx)])
            idx += 1
        if self.lora_enabled:
            self.lora_kernel_a.assign(ops.zeros(self.lora_kernel_a.shape))
            self.lora_kernel_b.assign(ops.zeros(self.lora_kernel_b.shape))