def set_input_embeddings(self, value: nn.Module):
        """Fallback setter that handles **~70%** of models in the code-base.

        Order of attempts:
        1. `self.<_input_embed_layer>` (direct attribute)
        2. `self.embeddings.<_input_embed_layer>` (nested embeddings for vision/audio models)
        3. `self.model.<_input_embed_layer>` (encoder/decoder models)
        4. delegate to the *base model* if one exists
        5. otherwise raise `NotImplementedError` so subclasses still can (and
            should) override for exotic layouts.
        """

        name = getattr(self, "_input_embed_layer", "embed_tokens")
        # 1) Direct attribute (most NLP models)
        if hasattr(self, name):
            setattr(self, name, value)
        # 2) Nested embeddings (e.g., self.embeddings.patch_embedding for vision models)
        elif hasattr(self, "embeddings") and hasattr(self.embeddings, name):
            setattr(self.embeddings, name, value)
        # 3) encoder/decoder and VLMs like `Gemma3nForConditionalGeneration`
        elif hasattr(self, "model") and hasattr(self.model, name):
            setattr(self.model, name, value)
        # 4) recurse once into the registered *base* model (e.g. for encoder/decoder)
        elif hasattr(self, "base_model") and self.base_model is not self:
            self.base_model.set_input_embeddings(value)
        else:
            raise NotImplementedError(
                f"`set_input_embeddings` not auto‑handled for {self.__class__.__name__}; please override in the subclass."
            )