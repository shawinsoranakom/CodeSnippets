def make_batched_videos(videos) -> list[Union[np.ndarray, "torch.Tensor", "URL", "Path"]]:
    """
    Ensure that the input is a list of videos. If the input is a single video, it is converted to a list of length 1.
    If the input is a batch of videos, it is converted to a list of 4D video arrays. Videos passed as list `PIL.Image`
    frames are converted to 4D arrays.

    We assume that all inputs in the list are in the same format, based on the type of the first element.

    Args:
        videos (`VideoInput`):
            Video inputs to turn into a list of videos.
    """
    # Early exit for deeply nested list of image frame paths. We shouldn't flatten them
    try:
        if isinstance(videos[0][0], list) and isinstance(videos[0][0][0], str):
            return [image_paths for sublist in videos for image_paths in sublist]
    except (IndexError, TypeError):
        pass

    if is_batched_video(videos):
        return convert_pil_frames_to_video(list(videos))
    elif isinstance(videos, str) or is_valid_video(videos):
        return convert_pil_frames_to_video([videos])
    # only one frame passed, thus we unsqueeze time dim
    elif is_valid_image(videos):
        if isinstance(videos, PIL.Image.Image):
            videos = np.array(videos)
        return [videos[None, ...]]
    elif not isinstance(videos, list):
        raise ValueError(
            f"Invalid video input. Expected either a list of video frames or an input of 4 or 5 dimensions, but got"
            f" type {type(videos)}."
        )

    # Recursively flatten any nested structure
    flat_videos_list = []
    for item in videos:
        if isinstance(item, str) or is_valid_video(item):
            flat_videos_list.append(item)
        elif isinstance(item, list) and item:
            flat_videos_list.extend(make_batched_videos(item))

    flat_videos_list = convert_pil_frames_to_video(flat_videos_list)
    return flat_videos_list