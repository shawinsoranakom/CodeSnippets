def _ensure_image_size_and_format(
    image_data: bytes, width: int, image_format: ImageFormat
) -> bytes:
    """Resize an image if it exceeds the given width, or if exceeds
    MAXIMUM_CONTENT_WIDTH. Ensure the image's format corresponds to the given
    ImageFormat. Return the (possibly resized and reformatted) image bytes.
    """
    image = Image.open(io.BytesIO(image_data))
    actual_width, actual_height = image.size

    if width < 0 and actual_width > MAXIMUM_CONTENT_WIDTH:
        width = MAXIMUM_CONTENT_WIDTH

    if width > 0 and actual_width > width:
        # We need to resize the image.
        new_height = int(1.0 * actual_height * width / actual_width)
        image = image.resize((width, new_height), resample=Image.BILINEAR)
        return _PIL_to_bytes(image, format=image_format, quality=90)

    ext = imghdr.what(None, image_data)
    if ext != image_format.lower():
        # We need to reformat the image.
        return _PIL_to_bytes(image, format=image_format, quality=90)

    # No resizing or reformatting necessary - return the original bytes.
    return image_data