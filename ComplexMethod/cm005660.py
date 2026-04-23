def video_metadata_validator(value: VideoMetadataType | None = None):
    if value is None:
        return

    valid_keys = ["total_num_frames", "fps", "width", "height", "duration", "video_backend", "frames_indices"]

    def check_dict_keys(d: dict[str, Any]) -> bool:
        return all(key in valid_keys for key in d.keys())

    if isinstance(value, Sequence) and isinstance(value[0], Sequence) and isinstance(value[0][0], dict):
        for sublist in value:
            for item in sublist:
                if not check_dict_keys(item):
                    raise ValueError(
                        f"Invalid keys found in video metadata. Valid keys: {valid_keys} got: {list(item.keys())}"
                    )

    elif isinstance(value, Sequence) and isinstance(value[0], dict):
        for item in value:
            if not check_dict_keys(item):
                raise ValueError(
                    f"Invalid keys found in video metadata. Valid keys: {valid_keys} got: {list(cast(dict, item).keys())}"
                )

    elif isinstance(value, dict):
        if not check_dict_keys(value):
            raise ValueError(
                f"Invalid keys found in video metadata. Valid keys: {valid_keys}, got: {list(value.keys())}"
            )