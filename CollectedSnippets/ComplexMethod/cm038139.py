def embed_multimodal(self, **kwargs: object) -> MultiModalEmbeddings:
        # Validate the multimodal input keyword arguments
        modalities = self._parse_and_validate_multimodal_inputs(**kwargs)
        if modalities is None:
            return []

        # # The result multimodal_embeddings is tuple of tensors, with each
        # tensor corresponding to a multimodal data item (image or video).
        multimodal_embeddings: tuple[torch.Tensor, ...] = ()

        # NOTE: It is important to iterate over the keys in this dictionary
        # to preserve the order of the modalities.
        for modality in modalities:
            if modality == "images":
                image_input = modalities["images"]
                if image_input["type"] == "image_embeds":
                    image_embeddings = image_input["data"]
                elif self.dynamic_resolution:
                    assert image_input["type"] == "pixel_values_dynamic"
                    image_embeddings = self._process_image_input_dynamic(image_input)
                else:
                    image_embeddings = self._process_image_input(image_input)
                multimodal_embeddings += tuple(image_embeddings)
            if modality == "videos":
                video_input = modalities["videos"]
                video_embeddings = self._process_video_input(video_input)
                multimodal_embeddings += tuple(video_embeddings)
            if modality == "audios":
                audio_input = modalities["audios"]
                audio_embeddings = self._process_audio_input(audio_input)
                multimodal_embeddings += tuple(audio_embeddings)

        return multimodal_embeddings