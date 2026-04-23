def make_nested_list_of_images(
    images: list[ImageInput] | ImageInput,
    expected_ndims: int = 3,
) -> list[ImageInput]:
    """
    Ensure that the output is a nested list of images.
    Args:
        images (`Union[list[ImageInput], ImageInput]`):
            The input image.
        expected_ndims (`int`, *optional*, defaults to 3):
            The expected number of dimensions for a single input image.
    Returns:
        list: A list of list of images or a list of 4d array of images.
    """
    # If it's a list of batches, it's already in the right format
    if (
        isinstance(images, (list, tuple))
        and all(isinstance(images_i, (list, tuple)) for images_i in images)
        and all(is_valid_list_of_images(images_i) or not images_i for images_i in images)
    ):
        return images

    # If it's a list of images, it's a single batch, so convert it to a list of lists
    if isinstance(images, (list, tuple)) and is_valid_list_of_images(images):
        if is_pil_image(images[0]) or images[0].ndim == expected_ndims:
            return [images]
        if images[0].ndim == expected_ndims + 1:
            return [list(image) for image in images]

    # If it's a single image, convert it to a list of lists
    if is_valid_image(images):
        if is_pil_image(images) or images.ndim == expected_ndims:
            return [[images]]
        if images.ndim == expected_ndims + 1:
            return [list(images)]

    raise ValueError("Invalid input type. Must be a single image, a list of images, or a list of batches of images.")