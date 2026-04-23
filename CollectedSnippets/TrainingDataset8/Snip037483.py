def _get_image_format_mimetype(image_format: ImageFormat) -> str:
    """Get the mimetype string for the given ImageFormat."""
    return f"image/{image_format.lower()}"