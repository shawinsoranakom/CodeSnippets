def _validate_ref_video_pixels(video: Input.Video, model_id: str, resolution: str, index: int) -> None:
    """Validate reference video pixel count against Seedance 2.0 model limits for the selected resolution."""
    model_limits = SEEDANCE2_REF_VIDEO_PIXEL_LIMITS.get(model_id)
    if not model_limits:
        return
    limits = model_limits.get(resolution)
    if not limits:
        return
    try:
        w, h = video.get_dimensions()
    except Exception:
        return
    pixels = w * h
    min_px = limits.get("min")
    max_px = limits.get("max")
    if min_px and pixels < min_px:
        raise ValueError(
            f"Reference video {index} is too small: {w}x{h} = {pixels:,}px. " f"Minimum is {min_px:,}px for this model."
        )
    if max_px and pixels > max_px:
        raise ValueError(
            f"Reference video {index} is too large: {w}x{h} = {pixels:,}px. "
            f"Maximum is {max_px:,}px for this model. Try downscaling the video."
        )