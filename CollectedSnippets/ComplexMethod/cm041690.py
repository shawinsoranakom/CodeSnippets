def _slice_mm_inputs_for_sample(
    mm_inputs: dict[str, Any],
    batch_imglens: list[int],
    batch_vidlens: list[int],
    batch_idx: int,
    images_per_subseq: Optional[list[int]] = None,
    videos_per_subseq: Optional[list[int]] = None,
    subseq_idx: Optional[int] = None,
) -> dict[str, Any]:
    r"""Slice mm_inputs for one batch sample, optionally for a single sub-sequence when packing.

    image_grid_thw / video_grid_thw have shape [num_items, 3]. Indices for sample batch_idx
    are batch_imglens[batch_idx] images and batch_vidlens[batch_idx] videos. When subseq_idx
    is given, further restrict to that sub-seq's counts via packed_*_counts.
    has_dummy_image=True means only batch[0] will be concated with fake image and no multimodal data.
    """
    image_start_idx = sum(batch_imglens[:batch_idx])
    image_end_idx = sum(batch_imglens[: batch_idx + 1])
    video_start_idx = sum(batch_vidlens[:batch_idx])
    video_end_idx = sum(batch_vidlens[: batch_idx + 1])

    if subseq_idx is not None and images_per_subseq is not None:
        image_start_idx += sum(images_per_subseq[:subseq_idx])
        image_end_idx = image_start_idx + images_per_subseq[subseq_idx]

    if subseq_idx is not None and videos_per_subseq is not None:
        video_start_idx += sum(videos_per_subseq[:subseq_idx])
        video_end_idx = video_start_idx + videos_per_subseq[subseq_idx]

    sliced_mm_inputs: dict[str, Any] = {}
    key_to_slice_meta = {
        "image_grid_thw": (image_start_idx, image_end_idx, True),
        "video_grid_thw": (video_start_idx, video_end_idx, True),
        "second_per_grid_ts": (video_start_idx, video_end_idx, False),  # qwen2.5vl
        "video_second_per_grid": (video_start_idx, video_end_idx, False),  # qwen omni
    }

    for key, (start_idx, end_idx, assign_none_when_empty) in key_to_slice_meta.items():
        if key not in mm_inputs:
            continue

        mm_value = mm_inputs[key]
        if mm_value is not None and end_idx > start_idx:
            sliced_mm_inputs[key] = mm_value[start_idx:end_idx]
        elif assign_none_when_empty:
            sliced_mm_inputs[key] = None

    return sliced_mm_inputs