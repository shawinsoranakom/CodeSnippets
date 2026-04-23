def _get_upscale_layer(method: T.Literal["resize_images", "subpixel", "upscale_dny",
                                         "upscale_fast", "upscale_hybrid", "upsample2d"],
                       filters: int,
                       activation: str | None = None,
                       upsamples: int | None = None,
                       interpolation: str | None = None) -> keras.layers.Layer:
    """ Obtain an instance of the requested upscale method.

    Parameters
    ----------
    method: str
        The user selected upscale method to use. One of `"resize_images"`, `"subpixel"`,
        `"upscale_dny"`, `"upscale_fast"`, `"upscale_hybrid"`, `"upsample2d"`
    filters: int
        The number of filters to use in the upscale layer
    activation: str, optional
        The activation function to use in the upscale layer. ``None`` to use no activation.
        Default: ``None``
    upsamples: int, optional
        Only used for UpSampling2D. If provided, then this is passed to the layer as the ``size``
        parameter. Default: ``None``
    interpolation: str, optional
        Only used for UpSampling2D. If provided, then this is passed to the layer as the
        ``interpolation`` parameter. Default: ``None``

    Returns
    -------
    :class:`keras.layers.Layer`
        The selected configured upscale layer
    """
    if method == "upsample2d":
        kwargs: dict[str, str | int] = {}
        if upsamples:
            kwargs["size"] = upsamples
        if interpolation:
            kwargs["interpolation"] = interpolation
        return kl.UpSampling2D(**kwargs)
    if method == "subpixel":
        return UpscaleBlock(filters, activation=activation)
    if method == "upscale_fast":
        return Upscale2xBlock(filters, activation=activation, fast=True)
    if method == "upscale_hybrid":
        return Upscale2xBlock(filters, activation=activation, fast=False)
    if method == "upscale_dny":
        return UpscaleDNYBlock(filters, activation=activation)
    return UpscaleResizeImagesBlock(filters, activation=activation)