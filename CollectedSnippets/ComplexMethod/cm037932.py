def get_language_model(self) -> VllmModel:
        """
        Returns the underlying language model used for text generation.

        This is typically the `torch.nn.Module` instance responsible for
        processing the merged multimodal embeddings and producing hidden states

        Returns:
            torch.nn.Module: The core language model component.
        """
        # Cached
        if self in _language_model_by_module:
            return _language_model_by_module[self]

        if self._language_model_names:
            mod = self
            for attr in common_prefix(
                [name.split(".") for name in self._language_model_names]
            ):
                if attr:
                    mod = getattr(mod, attr)

            if mod is not self and hasattr(mod, "embed_input_ids"):
                _language_model_by_module[self] = mod
                return mod

        # Fallback
        for mod in self.children():
            if hasattr(mod, "embed_input_ids"):
                _language_model_by_module[self] = mod
                return mod

        raise NotImplementedError(
            f"No language model found in {type(self).__name__}! "
            "You should initialize it via `_mark_language_model`."
        )