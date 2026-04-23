def validate_image_dimensions(
    image: torch.Tensor,
    min_width: int | None = None,
    max_width: int | None = None,
    min_height: int | None = None,
    max_height: int | None = None,
):
    height, width = get_image_dimensions(image)

    if min_width is not None and width < min_width:
        raise ValueError(f"Image width must be at least {min_width}px, got {width}px")
    if max_width is not None and width > max_width:
        raise ValueError(f"Image width must be at most {max_width}px, got {width}px")
    if min_height is not None and height < min_height:
        raise ValueError(f"Image height must be at least {min_height}px, got {height}px")
    if max_height is not None and height > max_height:
        raise ValueError(f"Image height must be at most {max_height}px, got {height}px")