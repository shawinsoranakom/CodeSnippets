def smart_resize(
    x,
    size,
    interpolation="bilinear",
    data_format="channels_last",
    **kwargs,
):
    """Resize images to a target size without aspect ratio distortion.

    Image datasets typically yield images that have each a different
    size. However, these images need to be batched before they can be
    processed by Keras layers. To be batched, images need to share the same
    height and width.

    You could simply do, in TF (or JAX equivalent):

    ```python
    size = (200, 200)
    ds = ds.map(lambda img: resize(img, size))
    ```

    However, if you do this, you distort the aspect ratio of your images, since
    in general they do not all have the same aspect ratio as `size`. This is
    fine in many cases, but not always (e.g. for image generation models
    this can be a problem).

    Note that passing the argument `preserve_aspect_ratio=True` to `resize`
    will preserve the aspect ratio, but at the cost of no longer respecting the
    provided target size.

    This calls for:

    ```python
    size = (200, 200)
    ds = ds.map(lambda img: smart_resize(img, size))
    ```

    Your output images will actually be `(200, 200)`, and will not be distorted.
    Instead, the parts of the image that do not fit within the target size
    get cropped out.

    The resizing process is:

    1. Take the largest centered crop of the image that has the same aspect
    ratio as the target size. For instance, if `size=(200, 200)` and the input
    image has size `(340, 500)`, we take a crop of `(340, 340)` centered along
    the width.
    2. Resize the cropped image to the target size. In the example above,
    we resize the `(340, 340)` crop to `(200, 200)`.

    Args:
        x: Input image or batch of images (as a tensor or NumPy array).
            Must be in format `(height, width, channels)`
            or `(batch_size, height, width, channels)`.
        size: Tuple of `(height, width)` integer. Target size.
        interpolation: String, interpolation to use for resizing.
            Supports `"bilinear"`, `"nearest"`, `"bicubic"`,
            `"lanczos3"`, `"lanczos5"`.
            Defaults to `"bilinear"`.
        data_format: `"channels_last"` or `"channels_first"`.

    Returns:
        Array with shape `(size[0], size[1], channels)`.
        If the input image was a NumPy array, the output is a NumPy array,
        and if it was a backend-native tensor,
        the output is a backend-native tensor.
    """
    backend_module = kwargs.pop("backend_module", None) or backend
    if kwargs:
        raise TypeError(
            "smart_resize() got unexpected keyword arguments: "
            f"{list(kwargs.keys())}"
        )
    if len(size) != 2:
        raise ValueError(
            f"Expected `size` to be a tuple of 2 integers, but got: {size}."
        )
    img = backend_module.convert_to_tensor(x)
    if len(img.shape) is not None:
        if len(img.shape) < 3 or len(img.shape) > 4:
            raise ValueError(
                "Expected an image array with shape `(height, width, "
                "channels)`, or `(batch_size, height, width, channels)`, but "
                f"got input with incorrect rank, of shape {img.shape}."
            )
    shape = backend_module.shape(img)
    if data_format == "channels_last":
        height, width = shape[-3], shape[-2]
    else:
        height, width = shape[-2], shape[-1]
    target_height, target_width = size

    # Set back to input height / width if crop_height / crop_width is not
    # smaller.
    if isinstance(height, int) and isinstance(width, int):
        # For JAX, we need to keep the slice indices as static integers
        crop_height = int(float(width * target_height) / target_width)
        crop_height = max(min(height, crop_height), 1)
        crop_width = int(float(height * target_width) / target_height)
        crop_width = max(min(width, crop_width), 1)
        crop_box_hstart = int(float(height - crop_height) / 2)
        crop_box_wstart = int(float(width - crop_width) / 2)
    else:
        crop_height = backend_module.cast(
            backend_module.cast(width * target_height, "float32")
            / target_width,
            "int32",
        )
        crop_height = backend_module.numpy.minimum(height, crop_height)
        crop_height = backend_module.numpy.maximum(crop_height, 1)
        crop_height = backend_module.cast(crop_height, "int32")

        crop_width = backend_module.cast(
            backend_module.cast(height * target_width, "float32")
            / target_height,
            "int32",
        )
        crop_width = backend_module.numpy.minimum(width, crop_width)
        crop_width = backend_module.numpy.maximum(crop_width, 1)
        crop_width = backend_module.cast(crop_width, "int32")

        crop_box_hstart = backend_module.cast(
            backend_module.cast(height - crop_height, "float32") / 2, "int32"
        )
        crop_box_wstart = backend_module.cast(
            backend_module.cast(width - crop_width, "float32") / 2, "int32"
        )

    if data_format == "channels_last":
        if len(img.shape) == 4:
            img = img[
                :,
                crop_box_hstart : crop_box_hstart + crop_height,
                crop_box_wstart : crop_box_wstart + crop_width,
                :,
            ]
        else:
            img = img[
                crop_box_hstart : crop_box_hstart + crop_height,
                crop_box_wstart : crop_box_wstart + crop_width,
                :,
            ]
    else:
        if len(img.shape) == 4:
            img = img[
                :,
                :,
                crop_box_hstart : crop_box_hstart + crop_height,
                crop_box_wstart : crop_box_wstart + crop_width,
            ]
        else:
            img = img[
                :,
                crop_box_hstart : crop_box_hstart + crop_height,
                crop_box_wstart : crop_box_wstart + crop_width,
            ]

    img = backend_module.image.resize(
        img, size=size, interpolation=interpolation, data_format=data_format
    )

    if isinstance(x, np.ndarray):
        return np.array(img)
    return img