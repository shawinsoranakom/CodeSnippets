def draw_bbox_with_number(i, bbox_list, page, c, rgb_config, fill_config, draw_bbox=True):
    new_rgb = [float(color) / 255 for color in rgb_config]
    page_data = bbox_list[i]
    # 强制转换为 float
    page_width, page_height = float(page.cropbox[2]), float(page.cropbox[3])

    for j, bbox in enumerate(page_data):
        # 确保bbox的每个元素都是float
        rect = cal_canvas_rect(page, bbox)  # Define the rectangle  

        if draw_bbox:
            if fill_config:
                c.setFillColorRGB(*new_rgb, 0.3)
                c.rect(rect[0], rect[1], rect[2], rect[3], stroke=0, fill=1)
            else:
                c.setStrokeColorRGB(*new_rgb)
                c.rect(rect[0], rect[1], rect[2], rect[3], stroke=1, fill=0)
        c.setFillColorRGB(*new_rgb, 1.0)
        c.setFontSize(size=10)

        c.saveState()
        rotation_obj = page.get("/Rotate", 0)
        try:
            rotation = int(rotation_obj) % 360  # cast rotation to int to handle IndirectObject
        except (ValueError, TypeError):
            logger.warning(f"Invalid /Rotate value: {rotation_obj!r}, defaulting to 0")
            rotation = 0

        if rotation == 0:
            c.translate(rect[0] + rect[2] + 2, rect[1] + rect[3] - 10)
        elif rotation == 90:
            c.translate(rect[0] + 10, rect[1] + rect[3] + 2)
        elif rotation == 180:
            c.translate(rect[0] - 2, rect[1] + 10)
        elif rotation == 270:
            c.translate(rect[0] + rect[2] - 10, rect[1] - 2)

        c.rotate(rotation)
        c.drawString(0, 0, str(j + 1))
        c.restoreState()

    return c