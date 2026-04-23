def _resolve_items(
    items_by_modality: dict[str, list[tuple[object, str | None]]],
    mm_processor: BaseMultiModalProcessor,
    modality_order: dict[str, list[str]],
) -> tuple[MultiModalDataDict, MultiModalUUIDDict]:
    if "image" in items_by_modality and "image_embeds" in items_by_modality:
        raise ValueError("Mixing raw image and embedding inputs is not allowed")
    if "audio" in items_by_modality and "audio_embeds" in items_by_modality:
        raise ValueError("Mixing raw audio and embedding inputs is not allowed")

    mm_data = {}
    mm_uuids = {}
    if "image_embeds" in items_by_modality:
        mm_data["image"] = _get_embeds_data(
            "image",
            [data for data, uuid in items_by_modality["image_embeds"]],
            mm_processor,
        )
        mm_uuids["image"] = [uuid for data, uuid in items_by_modality["image_embeds"]]
    if "image" in items_by_modality:
        mm_data["image"] = [data for data, uuid in items_by_modality["image"]]
        mm_uuids["image"] = [uuid for data, uuid in items_by_modality["image"]]
    if "audio_embeds" in items_by_modality:
        mm_data["audio"] = _get_embeds_data(
            "audio",
            [data for data, uuid in items_by_modality["audio_embeds"]],
            mm_processor,
        )
        mm_uuids["audio"] = [uuid for data, uuid in items_by_modality["audio_embeds"]]
    if "audio" in items_by_modality:
        mm_data["audio"] = [data for data, uuid in items_by_modality["audio"]]
        mm_uuids["audio"] = [uuid for data, uuid in items_by_modality["audio"]]
    if "video" in items_by_modality:
        mm_data["video"] = [data for data, uuid in items_by_modality["video"]]
        mm_uuids["video"] = [uuid for data, uuid in items_by_modality["video"]]
    if "vision_chunk" in items_by_modality:
        # Process vision_chunk items - extract from (data, modality) tuples
        # and convert to VisionChunk types with proper UUID handling
        processed_chunks, vision_chunk_uuids = _resolve_vision_chunk_items(
            items_by_modality["vision_chunk"],
            mm_processor,
            modality_order.get("vision_chunk", []),
        )
        mm_data["vision_chunk"] = processed_chunks
        mm_uuids["vision_chunk"] = vision_chunk_uuids

    return mm_data, mm_uuids