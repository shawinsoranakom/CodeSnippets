def split_pic(image, inverse_xy, width, height, overlap_ratio):
    if inverse_xy:
        from_w, from_h = image.height, image.width
        to_w, to_h = height, width
    else:
        from_w, from_h = image.width, image.height
        to_w, to_h = width, height
    h = from_h * to_w // from_w
    if inverse_xy:
        image = image.resize((h, to_w))
    else:
        image = image.resize((to_w, h))

    split_count = math.ceil((h - to_h * overlap_ratio) / (to_h * (1.0 - overlap_ratio)))
    y_step = (h - to_h) / (split_count - 1)
    for i in range(split_count):
        y = int(y_step * i)
        if inverse_xy:
            splitted = image.crop((y, 0, y + to_h, to_w))
        else:
            splitted = image.crop((0, y, to_w, y + to_h))
        yield splitted
