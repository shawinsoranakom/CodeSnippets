def _is_image_processor_class(func, parent_class):
    """
    Check if a function belongs to a ProcessorMixin class.

    Uses two methods:
    1. Check parent_class inheritance (if provided)
    2. Check if the source file is named processing_*.py (multimodal processors)
       vs image_processing_*.py, video_processing_*.py, etc. (single-modality processors)

    Args:
        func: The function to check
        parent_class: Optional parent class (if available)

    Returns:
        bool: True if this is a multimodal processor (inherits from ProcessorMixin), False otherwise
    """
    # First, check if parent_class is provided and use it
    if parent_class is not None:
        return "BaseImageProcessor" in parent_class.__name__ or any(
            "BaseImageProcessor" in base.__name__ for base in parent_class.__mro__
        )

    # If parent_class is None, check the filename
    # Multimodal processors are in files named "processing_*.py"
    # Single-modality processors are in "image_processing_*.py", "video_processing_*.py", etc.
    try:
        source_file = inspect.getsourcefile(func)
    except TypeError:
        return False
    if not source_file:
        return False

    # Exception for DummyProcessorForTest
    if func.__qualname__.split(".")[0] == "DummyForTestImageProcessorFast":
        return True

    filename = os.path.basename(source_file)

    # Multimodal processors are implemented in processing_*.py modules
    # (single-modality processors use image_processing_*, video_processing_*, etc.)self.
    return filename.startswith("image_processing_") and filename.endswith(".py")