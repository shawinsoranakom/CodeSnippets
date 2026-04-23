def validate_preprocess_arguments(
    do_rescale: bool | None = None,
    rescale_factor: float | None = None,
    do_normalize: bool | None = None,
    image_mean: float | list[float] | None = None,
    image_std: float | list[float] | None = None,
    do_pad: bool | None = None,
    pad_size: dict[str, int] | int | None = None,
    do_center_crop: bool | None = None,
    crop_size: dict[str, int] | None = None,
    do_resize: bool | None = None,
    size: dict[str, int] | None = None,
    resample: Union["PILImageResampling", "InterpolationMode", int] | None = None,
):
    """
    Checks validity of typically used arguments in an `ImageProcessor` `preprocess` method.
    Raises `ValueError` if arguments incompatibility is caught.
    Many incompatibilities are model-specific. `do_pad` sometimes needs `size_divisor`,
    sometimes `size_divisibility`, and sometimes `size`. New models and processors added should follow
    existing arguments when possible.

    """
    if do_rescale and rescale_factor is None:
        raise ValueError("`rescale_factor` must be specified if `do_rescale` is `True`.")

    if do_pad and pad_size is None:
        # Processors pad images using different args depending on the model, so the below check is pointless
        # but we keep it for BC for now. TODO: remove in v5
        # Usually padding can be called with:
        #   - "pad_size/size" if we're padding to specific values
        #   - "size_divisor" if we're padding to any value divisible by X
        #   - "None" if we're padding to the maximum size image in batch
        raise ValueError(
            "Depending on the model, `size_divisor` or `pad_size` or `size` must be specified if `do_pad` is `True`."
        )

    if do_normalize and (image_mean is None or image_std is None):
        raise ValueError("`image_mean` and `image_std` must both be specified if `do_normalize` is `True`.")

    if do_center_crop and crop_size is None:
        raise ValueError("`crop_size` must be specified if `do_center_crop` is `True`.")

    if do_resize and not (size is not None and resample is not None):
        raise ValueError("`size` and `resample` must be specified if `do_resize` is `True`.")