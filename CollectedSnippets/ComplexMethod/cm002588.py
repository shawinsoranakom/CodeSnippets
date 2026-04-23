def get_encoder(self, modality: str | None = None):
        """
        Best-effort lookup of the *encoder* module. If provided with `modality` argument,
        it looks for a modality-specific encoder in multimodal models (e.g. "image_encoder")
        By default the function returns model's text encoder if any, and otherwise returns `self`.

        Possible `modality` values are "image", "video" and "audio".
        """
        # NOTE: new models need to use existing names for layers if possible, so this list doesn't grow infinitely
        if modality in ["image", "video"]:
            possible_module_names = ["vision_tower", "visual", "vision_model", "vision_encoder", "image_tower"]
        elif modality == "audio":
            possible_module_names = ["audio_tower", "audio_encoder", "speech_encoder"]
        elif modality is None:
            possible_module_names = ["text_encoder", "encoder"]
        else:
            raise ValueError(f'Unnrecognized modality, has to be "image", "video" or "audio" but found {modality}')

        for name in possible_module_names:
            if hasattr(self, name):
                return getattr(self, name)

        if self.base_model is not self and hasattr(self.base_model, "get_encoder"):
            base_encoder = self.base_model.get_encoder(modality=modality)
            # Base model will always have attr `get_encoder` if inherited from `PreTrainedModel`
            # But it doesn't mean that the model has an encoder module, and we need to return `self`
            if base_encoder != self.base_model:
                return base_encoder

        # If this is a base transformer model (no encoder/model attributes), return self
        return self