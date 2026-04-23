def draw_bbox_multi(
    img_path: Path,
    output_path: Path,
    elem_list: list[AndroidElement],
    record_mode: bool = False,
    dark_mode: bool = False,
):
    imgcv = cv2.imread(str(img_path))
    count = 1
    for elem in elem_list:
        try:
            top_left = elem.bbox[0]
            bottom_right = elem.bbox[1]
            left, top = top_left[0], top_left[1]
            right, bottom = bottom_right[0], bottom_right[1]
            label = str(count)
            if record_mode:
                if elem.attrib == "clickable":
                    color = (250, 0, 0)
                elif elem.attrib == "focusable":
                    color = (0, 0, 250)
                else:
                    color = (0, 250, 0)
                imgcv = ps.putBText(
                    imgcv,
                    label,
                    text_offset_x=(left + right) // 2 + 10,
                    text_offset_y=(top + bottom) // 2 + 10,
                    vspace=10,
                    hspace=10,
                    font_scale=1,
                    thickness=2,
                    background_RGB=color,
                    text_RGB=(255, 250, 250),
                    alpha=0.5,
                )
            else:
                text_color = (10, 10, 10) if dark_mode else (255, 250, 250)
                bg_color = (255, 250, 250) if dark_mode else (10, 10, 10)
                imgcv = ps.putBText(
                    imgcv,
                    label,
                    text_offset_x=(left + right) // 2 + 10,
                    text_offset_y=(top + bottom) // 2 + 10,
                    vspace=10,
                    hspace=10,
                    font_scale=1,
                    thickness=2,
                    background_RGB=bg_color,
                    text_RGB=text_color,
                    alpha=0.5,
                )
        except Exception as e:
            logger.error(f"ERROR: An exception occurs while labeling the image\n{e}")
        count += 1
    cv2.imwrite(str(output_path), imgcv)
    return imgcv