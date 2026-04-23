def _make_packed_feature(
    *,
    packing_params: dict,
    pad_token_id: int,
    label_ignore_id: int,
    fake_image: Image.Image,
    vision_start_id: int | None = None,
    vision_end_id: int | None = None,
    image_pad_id: int | None = None,
) -> dict:
    r"""Build one packed sample using the new PackingParams schema."""
    sequence_boundaries = packing_params["sequence_boundaries"]
    image_subseq_ids = packing_params["image_subseq_ids"]
    video_subseq_ids = packing_params["video_subseq_ids"]
    audio_subseq_ids = packing_params["audio_subseq_ids"]
    unpadded_length = packing_params["unpadded_length"]
    right_padding_length = packing_params["right_padding_length"] # which only preserved in tests
    cutoff_plus_one = sequence_boundaries[-1]
    content_len = unpadded_length
    pad_len = right_padding_length
    assert content_len + pad_len == cutoff_plus_one
    assert sequence_boundaries[0] == 0
    assert sequence_boundaries[-1] == cutoff_plus_one

    content_ids = list(range(100, 100 + content_len))
    if vision_start_id is not None and vision_end_id is not None and image_pad_id is not None:
        image_counts_by_subseq = Counter(image_subseq_ids)
        for subseq_idx, image_count in sorted(image_counts_by_subseq.items()):
            if subseq_idx >= len(sequence_boundaries) - 1:
                continue

            subseq_start = sequence_boundaries[subseq_idx]
            subseq_end = sequence_boundaries[subseq_idx + 1]
            subseq_len = subseq_end - subseq_start
            if subseq_len < 3:
                continue

            # Build repeated image groups while preserving at least 3 tokens for each remaining image.
            injected_tokens: list[int] = []
            remaining = subseq_len
            for image_idx in range(image_count):
                remaining_images = image_count - image_idx
                min_reserved_for_rest = 3 * (remaining_images - 1)
                current_group_len = min(6, remaining - min_reserved_for_rest)
                if current_group_len < 3:
                    break

                group = [vision_start_id] + [image_pad_id] * max(1, current_group_len - 2) + [vision_end_id]
                injected_tokens.extend(group[:current_group_len])
                remaining -= current_group_len

            if injected_tokens:
                insert_end = subseq_start + len(injected_tokens)
                content_ids[subseq_start:insert_end] = injected_tokens

    input_ids = content_ids + [pad_token_id] * pad_len
    attention_mask = [1] * content_len + [0] * pad_len
    labels = [label_ignore_id] * cutoff_plus_one

    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "labels": labels,
        "images": [fake_image] * len(image_subseq_ids),
        "videos": [None] * len(video_subseq_ids),
        "audios": [None] * len(audio_subseq_ids),
        "packing_params": packing_params,
    }