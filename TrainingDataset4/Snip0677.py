def change_contrast(img: Image, level: int) -> Image:
    factor = (259 * (level + 255)) / (255 * (259 - level))

    def contrast(c: int) -> int:
        return int(128 + factor * (c - 128))

    return img.point(contrast)
