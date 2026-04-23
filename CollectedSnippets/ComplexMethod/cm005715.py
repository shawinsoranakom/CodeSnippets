def _get_base_kwargs_class_from_name(cls_name: str) -> str | None:
    """Map kwargs class name to base using naming conventions. Returns base class name or None."""
    if cls_name in _BASIC_KWARGS_NAMES:
        return cls_name
    if "ImageProcessorKwargs" in cls_name or cls_name.endswith("ImagesKwargs"):
        return "ImagesKwargs"
    if "ProcessorKwargs" in cls_name:
        return "ProcessingKwargs"
    if "VideoProcessorKwargs" in cls_name or cls_name.endswith("VideosKwargs"):
        return "VideosKwargs"
    if "AudioProcessorKwargs" in cls_name or cls_name.endswith("AudioKwargs"):
        return "AudioKwargs"
    if "TextKwargs" in cls_name:
        return "TextKwargs"
    return None