def add(self, modality: ModalityStr, item: _T) -> str | None:
        """
        Add a multi-modal item to the current prompt and returns the
        placeholder string to use, if any.

        An optional uuid can be added which serves as a unique identifier of the
        media.
        """
        input_modality = modality.replace("_embeds", "")
        original_modality = modality
        use_vision_chunk = (
            self.use_unified_vision_chunk_modality
            and original_modality in ["video", "image"]
        )

        # If use_unified_vision_chunk_modality is enabled,
        # map image/video to vision_chunk
        if use_vision_chunk:
            # To avoid validation fail
            # because models with use_unified_vision_chunk_modality=True
            # will only accept vision_chunk modality.
            input_modality = "vision_chunk"
            num_items = len(self._items_by_modality[input_modality]) + 1
        else:
            num_items = len(self._items_by_modality[original_modality]) + 1

        mm_config = self.model_config.multimodal_config
        if (
            mm_config is not None
            and mm_config.enable_mm_embeds
            and mm_config.get_limit_per_prompt(input_modality) == 0
            and original_modality.endswith("_embeds")
        ):
            # Skip validation: embeddings bypass limit when enable_mm_embeds=True
            pass
        else:
            self.mm_processor.info.validate_num_items(input_modality, num_items)

        # Track original modality for vision_chunk items
        if use_vision_chunk:
            self._items_by_modality[input_modality].append(item)  # type: ignore
            self._modality_order["vision_chunk"].append(original_modality)
        else:
            self._items_by_modality[original_modality].append(item)

        return self.model_cls.get_placeholder_str(modality, num_items)