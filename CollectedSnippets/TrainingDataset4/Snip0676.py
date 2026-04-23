def change_brightness(img: Image, level: float) -> Image:

    def brightness(c: int) -> float:
        return 128 + level + (c - 128)

    if not -255.0 <= level <= 255.0:
        raise ValueError("level must be between -255.0 (black) and 255.0 (white)")
    return img.point(brightness)
