def _extract_mm_features(
        engine_input: EngineInput,
    ) -> MultiModalFeatures | None:
        """Extract multimodal metadata from a rendered engine prompt.

        Returns ``None`` for text-only prompts.
        """
        if engine_input.get("type") != "multimodal":
            return None

        # At this point engine_input is a MultiModalInput TypedDict.
        mm_engine_input = cast(MultiModalInput, engine_input)
        mm_hashes: MultiModalHashes = mm_engine_input["mm_hashes"]
        raw_placeholders: MultiModalPlaceholders = mm_engine_input["mm_placeholders"]

        mm_placeholders = {
            modality: [
                PlaceholderRangeInfo(offset=p.offset, length=p.length) for p in ranges
            ]
            for modality, ranges in raw_placeholders.items()
        }

        # Serialize tensor data per modality.
        kwargs_data: dict[str, list[str | None]] | None = None
        if raw_mm_kwargs := mm_engine_input.get("mm_kwargs"):
            kwargs_data = {}
            for modality, items in raw_mm_kwargs.items():
                kwargs_data[modality] = [
                    encode_mm_kwargs_item(item) if item is not None else None
                    for item in items
                ]

        return MultiModalFeatures(
            mm_hashes=mm_hashes,
            mm_placeholders=mm_placeholders,
            kwargs_data=kwargs_data,
        )