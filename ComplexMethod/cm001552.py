def expand_crop_region(crop_region, processing_width, processing_height, image_width, image_height):
    """expands crop region get_crop_region() to match the ratio of the image the region will processed in; returns expanded region
    for example, if user drew mask in a 128x32 region, and the dimensions for processing are 512x512, the region will be expanded to 128x128."""

    x1, y1, x2, y2 = crop_region

    ratio_crop_region = (x2 - x1) / (y2 - y1)
    ratio_processing = processing_width / processing_height

    if ratio_crop_region > ratio_processing:
        desired_height = (x2 - x1) / ratio_processing
        desired_height_diff = int(desired_height - (y2-y1))
        y1 -= desired_height_diff//2
        y2 += desired_height_diff - desired_height_diff//2
        if y2 >= image_height:
            diff = y2 - image_height
            y2 -= diff
            y1 -= diff
        if y1 < 0:
            y2 -= y1
            y1 -= y1
        if y2 >= image_height:
            y2 = image_height
    else:
        desired_width = (y2 - y1) * ratio_processing
        desired_width_diff = int(desired_width - (x2-x1))
        x1 -= desired_width_diff//2
        x2 += desired_width_diff - desired_width_diff//2
        if x2 >= image_width:
            diff = x2 - image_width
            x2 -= diff
            x1 -= diff
        if x1 < 0:
            x2 -= x1
            x1 -= x1
        if x2 >= image_width:
            x2 = image_width

    return x1, y1, x2, y2