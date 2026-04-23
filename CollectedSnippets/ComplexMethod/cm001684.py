def crop_image(im, settings):
    """ Intelligently crop an image to the subject matter """

    scale_by = 1
    if is_landscape(im.width, im.height):
        scale_by = settings.crop_height / im.height
    elif is_portrait(im.width, im.height):
        scale_by = settings.crop_width / im.width
    elif is_square(im.width, im.height):
        if is_square(settings.crop_width, settings.crop_height):
            scale_by = settings.crop_width / im.width
        elif is_landscape(settings.crop_width, settings.crop_height):
            scale_by = settings.crop_width / im.width
        elif is_portrait(settings.crop_width, settings.crop_height):
            scale_by = settings.crop_height / im.height

    im = im.resize((int(im.width * scale_by), int(im.height * scale_by)))
    im_debug = im.copy()

    focus = focal_point(im_debug, settings)

    # take the focal point and turn it into crop coordinates that try to center over the focal
    # point but then get adjusted back into the frame
    y_half = int(settings.crop_height / 2)
    x_half = int(settings.crop_width / 2)

    x1 = focus.x - x_half
    if x1 < 0:
        x1 = 0
    elif x1 + settings.crop_width > im.width:
        x1 = im.width - settings.crop_width

    y1 = focus.y - y_half
    if y1 < 0:
        y1 = 0
    elif y1 + settings.crop_height > im.height:
        y1 = im.height - settings.crop_height

    x2 = x1 + settings.crop_width
    y2 = y1 + settings.crop_height

    crop = [x1, y1, x2, y2]

    results = []

    results.append(im.crop(tuple(crop)))

    if settings.annotate_image:
        d = ImageDraw.Draw(im_debug)
        rect = list(crop)
        rect[2] -= 1
        rect[3] -= 1
        d.rectangle(rect, outline=GREEN)
        results.append(im_debug)
        if settings.desktop_view_image:
            im_debug.show()

    return results