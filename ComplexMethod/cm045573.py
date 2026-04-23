def _validate_base64_image(
        self, base64_string: str, max_size_mb: int = 10
    ) -> tuple[bool, str]:
        """
        Validate base64 image data.
        Args:
            base64_string: The base64 encoded image data
            max_size_mb: Maximum allowed image size in megabytes
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not base64_string or len(base64_string) < 10:
                return False, "Base64 string is empty or too short"
            if base64_string.startswith("data:"):
                try:
                    base64_string = base64_string.split(",", 1)[1]
                except (IndexError, ValueError):
                    return False, "Invalid data URL format"
            import re

            if not re.match(r"^[A-Za-z0-9+/]*={0,2}$", base64_string):
                return False, "Invalid base64 characters detected"
            if len(base64_string) % 4 != 0:
                return False, "Invalid base64 string length"
            try:
                image_data = base64.b64decode(base64_string, validate=True)
            except Exception as e:
                return False, f"Base64 decoding failed: {str(e)}"
            max_size_bytes = max_size_mb * 1024 * 1024
            if len(image_data) > max_size_bytes:
                return False, f"Image size exceeds limit ({max_size_bytes} bytes)"
            try:
                image_stream = io.BytesIO(image_data)
                with Image.open(image_stream) as img:
                    img.verify()
                    supported_formats = {"JPEG", "PNG", "GIF", "BMP", "WEBP", "TIFF"}
                    if img.format not in supported_formats:
                        return False, f"Unsupported image format: {img.format}"
                    image_stream.seek(0)
                    with Image.open(image_stream) as img_check:
                        width, height = img_check.size
                        max_dimension = 8192
                        if width > max_dimension or height > max_dimension:
                            return (
                                False,
                                f"Image dimensions exceed limit ({max_dimension}x{max_dimension})",
                            )
                        if width < 1 or height < 1:
                            return False, f"Invalid image dimensions: {width}x{height}"
            except Exception as e:
                return False, f"Invalid image data: {str(e)}"
            return True, "Valid image"
        except Exception as e:
            logger.error(f"Unexpected error during base64 image validation: {e}")
            return False, f"Validation error: {str(e)}"