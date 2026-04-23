def validate_and_format_image_pairs(images: ImageInput):
    error_message = (
        "Input images must be a one of the following :",
        " - A pair of PIL images.",
        " - A pair of 3D arrays.",
        " - A list of pairs of PIL images.",
        " - A list of pairs of 3D arrays.",
    )

    def _is_valid_image(image):
        """images is a PIL Image or a 3D array."""
        return is_pil_image(image) or (
            is_valid_image(image) and get_image_type(image) != ImageType.PIL and len(image.shape) == 3
        )

    if isinstance(images, list):
        if len(images) == 2 and all((_is_valid_image(image)) for image in images):
            return images
        if all(
            isinstance(image_pair, list)
            and len(image_pair) == 2
            and all(_is_valid_image(image) for image in image_pair)
            for image_pair in images
        ):
            return [image for image_pair in images for image in image_pair]
    raise ValueError(error_message)