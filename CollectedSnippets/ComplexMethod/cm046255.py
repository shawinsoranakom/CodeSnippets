def check_source(
    source: str | int | Path | list | tuple | np.ndarray | Image.Image | torch.Tensor,
) -> tuple[Any, bool, bool, bool, bool, bool]:
    """Check the type of input source and return corresponding flag values.

    Args:
        source (str | int | Path | list | tuple | np.ndarray | PIL.Image | torch.Tensor): The input source to check.

    Returns:
        source (str | int | Path | list | tuple | np.ndarray | PIL.Image | torch.Tensor): The processed source.
        webcam (bool): Whether the source is a webcam.
        screenshot (bool): Whether the source is a screenshot.
        from_img (bool): Whether the source is an image or list of images.
        in_memory (bool): Whether the source is an in-memory object.
        tensor (bool): Whether the source is a torch.Tensor.

    Examples:
        Check a file path source
        >>> source, webcam, screenshot, from_img, in_memory, tensor = check_source("image.jpg")

        Check a webcam source
        >>> source, webcam, screenshot, from_img, in_memory, tensor = check_source(0)
    """
    webcam, screenshot, from_img, in_memory, tensor = False, False, False, False, False
    if isinstance(source, (str, int, Path)):  # int for local usb camera
        source = str(source)
        source_lower = source.lower()
        is_url = source_lower.startswith(("https://", "http://", "rtsp://", "rtmp://", "tcp://"))
        is_file = (urlsplit(source_lower).path if is_url else source_lower).rpartition(".")[-1] in (
            IMG_FORMATS | VID_FORMATS
        )
        webcam = source.isnumeric() or source.endswith(".streams") or (is_url and not is_file)
        screenshot = source_lower == "screen"
        if is_url and is_file:
            source = check_file(source)  # download
    elif isinstance(source, LOADERS):
        in_memory = True
    elif isinstance(source, (list, tuple)):
        source = autocast_list(source)  # convert all list elements to PIL or np arrays
        from_img = True
    elif isinstance(source, (Image.Image, np.ndarray)):
        from_img = True
    elif isinstance(source, torch.Tensor):
        tensor = True
    else:
        raise TypeError("Unsupported image type. For supported types see https://docs.ultralytics.com/modes/predict")

    return source, webcam, screenshot, from_img, in_memory, tensor