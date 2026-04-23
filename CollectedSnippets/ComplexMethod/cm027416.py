def _crop_image(image, opts):
    """Crop image."""
    try:
        img = _precheck_image(image, opts)
    except ValueError:
        return image

    quality = opts.quality or DEFAULT_QUALITY
    (old_width, old_height) = img.size
    old_size = len(image)
    if opts.top is None:
        opts.top = 0
    if opts.left is None:
        opts.left = 0
    if opts.max_width is None or opts.max_width > old_width - opts.left:
        opts.max_width = old_width - opts.left
    if opts.max_height is None or opts.max_height > old_height - opts.top:
        opts.max_height = old_height - opts.top

    img = img.crop(
        (opts.left, opts.top, opts.left + opts.max_width, opts.top + opts.max_height)
    )
    imgbuf = io.BytesIO()
    img.save(imgbuf, "JPEG", optimize=True, quality=quality)
    newimage = imgbuf.getvalue()

    _LOGGER.debug(
        "Cropped image from (%dx%d - %d bytes) to (%dx%d - %d bytes)",
        old_width,
        old_height,
        old_size,
        opts.max_width,
        opts.max_height,
        len(newimage),
    )
    return newimage