def set_encoder(self, encoder, modality: str | None = None):
        """
        Symmetric setter. Mirrors the lookup logic used in `get_encoder`.
        """

        # NOTE: new models need to use existing names for layers if possible, so this list doesn't grow infinitely
        if modality in ["image", "video"]:
            possible_module_names = ["vision_tower", "visual", "vision_model", "vision_encoder", "image_tower"]
        elif modality == "audio":
            possible_module_names = ["audio_tower", "audio_encoder"]
        elif modality is None:
            possible_module_names = ["text_encoder", "encoder"]
        else:
            raise ValueError(f'Unnrecognized modality, has to be "image", "video" or "audio" but found {modality}')

        for name in possible_module_names:
            if hasattr(self, name):
                setattr(self, name, encoder)
                return

        if self.base_model is not self:
            if hasattr(self.base_model, "set_encoder"):
                self.base_model.set_encoder(encoder, modality=modality)
            else:
                self.model = encoder