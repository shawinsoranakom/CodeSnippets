def validate_video_dimensions(
    video: Input.Video,
    min_width: int | None = None,
    max_width: int | None = None,
    min_height: int | None = None,
    max_height: int | None = None,
):
    try:
        width, height = video.get_dimensions()
    except Exception as e:
        logging.error("Error getting dimensions of video: %s", e)
        return

    if min_width is not None and width < min_width:
        raise ValueError(f"Video width must be at least {min_width}px, got {width}px")
    if max_width is not None and width > max_width:
        raise ValueError(f"Video width must be at most {max_width}px, got {width}px")
    if min_height is not None and height < min_height:
        raise ValueError(f"Video height must be at least {min_height}px, got {height}px")
    if max_height is not None and height > max_height:
        raise ValueError(f"Video height must be at most {max_height}px, got {height}px")