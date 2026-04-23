def image_grid(imgs, batch_size=1, rows=None):
    if rows is None:
        if opts.n_rows > 0:
            rows = opts.n_rows
        elif opts.n_rows == 0:
            rows = batch_size
        elif opts.grid_prevent_empty_spots:
            rows = math.floor(math.sqrt(len(imgs)))
            while len(imgs) % rows != 0:
                rows -= 1
        else:
            rows = math.sqrt(len(imgs))
            rows = round(rows)
    if rows > len(imgs):
        rows = len(imgs)

    cols = math.ceil(len(imgs) / rows)

    params = script_callbacks.ImageGridLoopParams(imgs, cols, rows)
    script_callbacks.image_grid_callback(params)

    w, h = map(max, zip(*(img.size for img in imgs)))
    grid_background_color = ImageColor.getcolor(opts.grid_background_color, 'RGB')
    grid = Image.new('RGB', size=(params.cols * w, params.rows * h), color=grid_background_color)

    for i, img in enumerate(params.imgs):
        img_w, img_h = img.size
        w_offset, h_offset = 0 if img_w == w else (w - img_w) // 2, 0 if img_h == h else (h - img_h) // 2
        grid.paste(img, box=(i % params.cols * w + w_offset, i // params.cols * h + h_offset))

    return grid