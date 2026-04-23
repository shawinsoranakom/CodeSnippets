def validate_image_content_type(
    file_path: str,
    content: bytes | None = None,
    storage_service: StorageService | None = None,
    resolve_path: Callable[[str], str] | None = None,
) -> tuple[bool, str | None]:
    """Validate that an image file's content matches its declared extension.

    This prevents errors like "Image does not match the provided media type image/png"
    when a JPEG file is saved with a .png extension.

    Only rejects files when we can definitively detect a mismatch. Files with
    unrecognized content are allowed through (they may fail later, but that's
    better than false positives blocking valid files).

    Args:
        file_path: Path to the image file
        content: Optional pre-read file content bytes. If not provided, will read from file.
        storage_service: Optional storage service instance for S3 files
        resolve_path: Optional function to resolve relative paths

    Returns:
        tuple[bool, str | None]: (is_valid, error_message)
            - (True, None) if the content matches the extension, is unrecognized, or file is not an image
            - (False, error_message) if there's a definite mismatch
    """
    # Get the file extension
    path_obj = Path(file_path)
    extension = path_obj.suffix[1:].lower() if path_obj.suffix else ""

    # Only validate image files
    image_extensions = {"jpeg", "jpg", "png", "gif", "webp", "bmp", "tiff"}
    if extension not in image_extensions:
        return True, None

    # Read content if not provided
    if content is None:
        try:
            content = run_until_complete(read_file_bytes(file_path, storage_service, resolve_path))
        except (FileNotFoundError, ValueError):
            # Can't read file - let it pass, will fail later with better error
            return True, None

    # Detect actual image type
    detected_type = detect_image_type_from_bytes(content)

    # If we can't detect the type, the file is not a valid image
    if detected_type is None:
        return False, (
            f"File '{path_obj.name}' has extension '.{extension}' but its content "
            f"is not a valid image format. The file may be corrupted, empty, or not a real image."
        )

    # Normalize extensions for comparison (jpg == jpeg, tif == tiff)
    extension_normalized = "jpeg" if extension == "jpg" else extension
    detected_normalized = "jpeg" if detected_type == "jpg" else detected_type

    if extension_normalized != detected_normalized:
        return False, (
            f"File '{path_obj.name}' has extension '.{extension}' but contains "
            f"'{detected_type.upper()}' image data. This mismatch will cause API errors. "
            f"Please rename the file with the correct extension '.{detected_type}' or "
            f"re-save it in the correct format."
        )

    return True, None