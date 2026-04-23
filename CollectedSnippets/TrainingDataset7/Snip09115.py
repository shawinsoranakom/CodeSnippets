def validate_image_file_extension(value):
    return FileExtensionValidator(allowed_extensions=get_available_image_extensions())(
        value
    )