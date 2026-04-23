def _image_is_gif(image: PILImage) -> bool:
    return bool(image.format == "GIF")