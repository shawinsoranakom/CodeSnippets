def prepare_image_inputs(
    batch_size,
    min_resolution,
    max_resolution,
    num_channels,
    size_divisor=None,
    equal_resolution=False,
    numpify=False,
    torchify=False,
):
    """This function prepares a list of PIL images, or a list of numpy arrays if one specifies numpify=True,
    or a list of PyTorch tensors if one specifies torchify=True.

    One can specify whether the images are of the same resolution or not.
    """

    assert not (numpify and torchify), "You cannot specify both numpy and PyTorch tensors at the same time"

    image_inputs = []
    for i in range(batch_size):
        if equal_resolution:
            width = height = max_resolution
        else:
            # To avoid getting image width/height 0
            if size_divisor is not None:
                # If `size_divisor` is defined, the image needs to have width/size >= `size_divisor`
                min_resolution = max(size_divisor, min_resolution)
            width, height = np.random.choice(np.arange(min_resolution, max_resolution), 2)
        image_inputs.append(np.random.randint(255, size=(num_channels, width, height), dtype=np.uint8))

    if not numpify and not torchify:
        # PIL expects the channel dimension as last dimension
        image_inputs = [Image.fromarray(np.moveaxis(image, 0, -1)) for image in image_inputs]

    if torchify:
        image_inputs = [torch.from_numpy(image) for image in image_inputs]

    if numpify:
        # Numpy images are typically in channels last format
        image_inputs = [image.transpose(1, 2, 0) for image in image_inputs]

    return image_inputs