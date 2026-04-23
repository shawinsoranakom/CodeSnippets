def get_width_height(
    aspect_ratio: str,
    width: Optional[int] = None,
    height: Optional[int] = None
) -> tuple[int, int]:
    if aspect_ratio == "1:1":
        return width or 1024, height or 1024
    elif aspect_ratio == "16:9":
        return width or 832, height or 480
    elif aspect_ratio == "9:16":
        return width or 480, height or 832,
    return width, height