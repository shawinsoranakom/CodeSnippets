def _validate_image_format_string(
    image_data: Union[bytes, PILImage], format: str
) -> ImageFormat:
    """Return either "JPEG", "PNG", or "GIF", based on the input `format` string.

    - If `format` is "JPEG" or "JPG" (or any capitalization thereof), return "JPEG"
    - If `format` is "PNG" (or any capitalization thereof), return "PNG"
    - For all other strings, return "PNG" if the image has an alpha channel,
    "GIF" if the image is a GIF, and "JPEG" otherwise.
    """
    format = format.upper()
    if format == "JPEG" or format == "PNG":
        return cast(ImageFormat, format)

    # We are forgiving on the spelling of JPEG
    if format == "JPG":
        return "JPEG"

    if isinstance(image_data, bytes):
        pil_image = Image.open(io.BytesIO(image_data))
    else:
        pil_image = image_data

    if _image_is_gif(pil_image):
        return "GIF"

    if _image_may_have_alpha_channel(pil_image):
        return "PNG"

    return "JPEG"