def save_own_variables(self, store):
        # Do nothing if the layer isn't yet built
        if not self.built:
            return
        mode = self.quantization_mode
        if mode not in self.variable_serialization_spec:
            raise self._quantization_mode_error(mode)

        # Embeddings plus optional merged LoRA-aware scale/zero (returns
        # (embeddings, None, None) for `None` mode).
        embeddings_value, merged_embeddings_scale, merged_embeddings_zero = (
            self._get_embeddings_with_merged_lora()
        )
        idx = 0
        for name in self.variable_serialization_spec[mode]:
            if name == "embeddings":
                store[str(idx)] = embeddings_value
            elif name == "embeddings_zero":
                if merged_embeddings_zero is None:
                    # embeddings_zero only exists for sub-channel int4
                    # quantization
                    continue
                store[str(idx)] = merged_embeddings_zero
            elif name == "g_idx" and not hasattr(self, "g_idx"):
                # g_idx only exists for sub-channel int4 quantization
                continue
            elif name == "embeddings_scale" and mode in ("int4", "int8"):
                # For int4/int8, the merged LoRA scale (if any) comes from
                # `_get_embeddings_with_merged_lora()`
                store[str(idx)] = merged_embeddings_scale
            else:
                # Generic handling for subclass variables:
                # Check if the attribute exists on the instance before saving.
                # This supports optional variables in subclasses (e.g.,
                # `reverse_embeddings_zero` in ReversibleEmbedding) that are
                # present in the spec but may not exist on the object depending
                # on configuration (e.g., per-channel vs. sub-channel).
                if not hasattr(self, name):
                    continue
                store[str(idx)] = getattr(self, name)
            idx += 1