def get_size_with_aspect_ratio_yolos(
    image_size: tuple[int, int], size: int, max_size: int | None = None, mod_size: int = 16
) -> tuple[int, int]:
    """
    Computes the output image size given the input image size and the desired output size, while ensuring that both
    height and width are multiples of `mod_size`.

    This mirrors the YOLOS-specific behavior used in the torch/fast backends and is required so that all YOLOS
    image processing backends (PIL, torchvision, fast) produce identical output shapes.
    """
    height, width = image_size
    raw_size = None
    if max_size is not None:
        min_original_size = float(min((height, width)))
        max_original_size = float(max((height, width)))
        if max_original_size / min_original_size * size > max_size:
            raw_size = max_size * min_original_size / max_original_size
            size = int(round(raw_size))

    if width < height:
        ow = size
        if max_size is not None and raw_size is not None:
            oh = int(raw_size * height / width)
        else:
            oh = int(size * height / width)
    elif (height <= width and height == size) or (width <= height and width == size):
        oh, ow = height, width
    else:
        oh = size
        if max_size is not None and raw_size is not None:
            ow = int(raw_size * width / height)
        else:
            ow = int(size * width / height)

    if mod_size is not None:
        ow = ow - (ow % mod_size)
        oh = oh - (oh % mod_size)

    return (oh, ow)