def _resize_image(image, opts):
    """Resize image."""
    try:
        img = _precheck_image(image, opts)
    except ValueError:
        return image

    quality = opts.quality or DEFAULT_QUALITY
    new_width = opts.max_width
    (old_width, old_height) = img.size
    old_size = len(image)

    # If no max_width specified, only apply quality changes if requested
    if new_width is None:
        if opts.quality is None:
            return image
        imgbuf = io.BytesIO()
        img.save(imgbuf, "JPEG", optimize=True, quality=quality)
        return imgbuf.getvalue()

    if old_width <= new_width:
        if opts.quality is None:
            _LOGGER.debug("Image is smaller-than/equal-to requested width")
            return image
        new_width = old_width

    scale = new_width / float(old_width)
    new_height = int(float(old_height) * float(scale))

    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    imgbuf = io.BytesIO()
    img.save(imgbuf, "JPEG", optimize=True, quality=quality)
    newimage = imgbuf.getvalue()
    if not opts.force_resize and len(newimage) >= old_size:
        _LOGGER.debug(
            (
                "Using original image (%d bytes) "
                "because resized image (%d bytes) is not smaller"
            ),
            old_size,
            len(newimage),
        )
        return image

    _LOGGER.debug(
        "Resized image from (%dx%d - %d bytes) to (%dx%d - %d bytes)",
        old_width,
        old_height,
        old_size,
        new_width,
        new_height,
        len(newimage),
    )
    return newimage