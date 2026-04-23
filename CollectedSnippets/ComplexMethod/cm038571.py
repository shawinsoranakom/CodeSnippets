def _resolve_vision_chunk_items(
    vision_chunk_items: list[tuple[object, str | None]],
    mm_processor: BaseMultiModalProcessor,
    vision_chunks_modality_order: list[str],
):
    # Process vision_chunk items - extract from (data, modality) tuples
    # and convert to VisionChunk types with proper UUID handling
    vision_chunks_uuids = [uuid for data, uuid in vision_chunk_items]

    assert len(vision_chunk_items) == len(vision_chunks_modality_order), (
        f"vision_chunk items ({len(vision_chunk_items)}) and "
        f"modality_order ({len(vision_chunks_modality_order)}) must have same length"
    )

    processed_chunks: list[VisionChunk] = []
    video_idx = 0
    for inner_modality, (data, uuid) in zip(
        vision_chunks_modality_order, vision_chunk_items
    ):
        if inner_modality == "image":
            # Cast data to proper type for image
            # Use .media (PIL.Image) directly to avoid redundant
            # bytes→PIL conversion in media_processor
            if hasattr(data, "media"):
                image_data = data.media  # type: ignore[union-attr]
                processed_chunks.append(
                    VisionChunkImage(type="image", image=image_data, uuid=uuid)
                )
            else:
                processed_chunks.append(data)  # type: ignore[arg-type]
        elif inner_modality == "video":
            # For video, we may need to split into chunks
            # if processor supports it
            # For now, just wrap as a video chunk placeholder
            if hasattr(mm_processor, "split_video_chunks") and data is not None:
                try:
                    video_uuid = uuid or random_uuid()
                    # video await result is (video_data, video_meta) tuple
                    if isinstance(data, tuple) and len(data) >= 1:
                        video_data = data[0]
                    else:
                        video_data = data
                    video_chunks = mm_processor.split_video_chunks(video_data)
                    for i, vc in enumerate(video_chunks):
                        processed_chunks.append(
                            VisionChunkVideo(
                                type="video_chunk",
                                video_chunk=vc["video_chunk"],
                                uuid=f"{video_uuid}-{i}",
                                video_idx=video_idx,
                                prompt=vc["prompt"],
                            )
                        )
                    video_idx += 1
                except Exception as e:
                    logger.warning("Failed to split video chunks: %s", e)
                    processed_chunks.append(data)  # type: ignore[arg-type]
            else:
                processed_chunks.append(data)  # type: ignore[arg-type]
    return processed_chunks, vision_chunks_uuids