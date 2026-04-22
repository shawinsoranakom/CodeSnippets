def _PIL_to_bytes(
    image: PILImage,
    format: ImageFormat = "JPEG",
    quality: int = 100,
) -> bytes:
    """Convert a PIL image to bytes."""
    tmp = io.BytesIO()

    # User must have specified JPEG, so we must convert it
    if format == "JPEG" and _image_may_have_alpha_channel(image):
        image = image.convert("RGB")

    image.save(tmp, format=format, quality=quality)

    return tmp.getvalue()