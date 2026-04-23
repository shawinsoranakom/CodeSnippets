def load_own_variables(self, store):
        if not self.lora_enabled:
            self._check_load_own_variables(store)
        # Do nothing if the layer isn't yet built
        if not self.built:
            return
        mode = self.quantization_mode
        if mode not in self.variable_serialization_spec:
            raise self._quantization_mode_error(mode)

        idx = 0
        for name in self.variable_serialization_spec[mode]:
            if name == "embeddings":
                self._embeddings.assign(store[str(idx)])
            elif name == "embeddings_zero" and not hasattr(
                self, "embeddings_zero"
            ):
                # embeddings_zero only exists for sub-channel int4 quantization
                continue
            elif name == "g_idx" and not hasattr(self, "g_idx"):
                # g_idx only exists for sub-channel int4 quantization
                continue
            else:
                # Generic handling for subclass variables:
                # Check if the attribute exists before attempting to assign.
                # If the variable is in the spec but missing from the object,
                # we skip it to prevent AttributeError.
                if not hasattr(self, name):
                    continue
                getattr(self, name).assign(store[str(idx)])
            idx += 1
        if self.lora_enabled:
            self.lora_embeddings_a.assign(
                ops.zeros(self.lora_embeddings_a.shape)
            )
            self.lora_embeddings_b.assign(
                ops.zeros(self.lora_embeddings_b.shape)
            )