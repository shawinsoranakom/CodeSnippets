def get_input_embeddings(self) -> nn.Module:
        """
        Returns the model's input embeddings.

        Returns:
            `nn.Module`: A torch module mapping vocabulary to hidden states.
        """

        name = getattr(self, "_input_embed_layer", "embed_tokens")

        # 1) Direct attribute (most NLP models).
        if (default_embedding := getattr(self, name, None)) is not None:
            return default_embedding
        # 2) Nested embeddings (e.g., self.embeddings.patch_embedding for vision/audio models).
        if hasattr(self, "embeddings") and hasattr(self.embeddings, name):
            return getattr(self.embeddings, name)
        # 3) Encoder/decoder wrappers (e.g., `self.model.embed_tokens` or similar overrides).
        if hasattr(self, "model") and hasattr(self.model, name):
            return getattr(self.model, name)

        if hasattr(self, "base_model"):
            base_model = self.base_model
            if base_model is not None and base_model is not self:
                return base_model.get_input_embeddings()

        raise NotImplementedError(
            f"`get_input_embeddings` not auto‑handled for {self.__class__.__name__}; please override in the subclass."
        )