def validate_image_pairs(images: Any) -> Sequence[Sequence[ImagePair]]:
    error_message = (
        "Input images must be a one of the following :",
        " - A pair of images.",
        " - A list of pairs of images.",
    )

    def _is_valid_image(image):
        """images is a PIL Image or a string."""
        return is_pil_image(image) or isinstance(image, str)

    if isinstance(images, Sequence):
        if len(images) == 2 and all((_is_valid_image(image)) for image in images):
            return [images]
        if all(
            isinstance(image_pair, Sequence)
            and len(image_pair) == 2
            and all(_is_valid_image(image) for image in image_pair)
            for image_pair in images
        ):
            return images
    raise ValueError(error_message)