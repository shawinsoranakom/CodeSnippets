def to_image(image: ImageType, is_svg: bool = False) -> Image.Image:
    """
    Converts the input image to a PIL Image object.

    Args:
        image (Union[str, bytes, Image]): The input image.

    Returns:
        Image: The converted PIL Image object.
    """
    if not has_requirements:
        raise MissingRequirementsError('Install "pillow" package for images')

    if isinstance(image, str) and image.startswith("data:"):
        is_data_uri_an_image(image)
        image = extract_data_uri(image)

    if is_svg:
        try:
            import cairosvg
        except ImportError:
            raise MissingRequirementsError('Install "cairosvg" package for svg images')
        if not isinstance(image, bytes):
            image = image.read()
        buffer = BytesIO()
        cairosvg.svg2png(image, write_to=buffer)
        return Image.open(buffer)

    if isinstance(image, bytes):
        is_accepted_format(image)
        return Image.open(BytesIO(image))
    elif not isinstance(image, Image.Image):
        image = Image.open(image)
        image.load()
        return image

    return image