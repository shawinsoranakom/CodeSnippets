def image_process(source, size=(0, 0), verify_resolution=False, quality=0, expand=False, crop=None, colorize=False, output_format='', padding=False):
    """Process the `source` image by executing the given operations and
    return the result image.
    """
    if not source or ((not size or (not size[0] and not size[1])) and not verify_resolution and not quality and not crop and not colorize and not output_format and not padding):
        # for performance: don't do anything if the image is falsy or if
        # no operations have been requested
        return source

    image = ImageProcess(source, verify_resolution)
    if size:
        if crop:
            center_x = 0.5
            center_y = 0.5
            if crop == 'top':
                center_y = 0
            elif crop == 'bottom':
                center_y = 1
            image.crop_resize(max_width=size[0], max_height=size[1], center_x=center_x, center_y=center_y)
        else:
            image.resize(max_width=size[0], max_height=size[1], expand=expand)
    if padding:
        image.add_padding(padding)
    if colorize:
        image.colorize(colorize if isinstance(colorize, tuple) else None)
    return image.image_quality(quality=quality, output_format=output_format)