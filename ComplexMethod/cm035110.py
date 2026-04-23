def draw_structure_result(image, result, font_path):
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)
    boxes, txts, scores = [], [], []

    img_layout = image.copy()
    draw_layout = ImageDraw.Draw(img_layout)
    text_color = (255, 255, 255)
    text_background_color = (80, 127, 255)
    catid2color = {}
    font_size = 15
    font = ImageFont.truetype(font_path, font_size, encoding="utf-8")

    for region in result:
        if region["type"] not in catid2color:
            box_color = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
            )
            catid2color[region["type"]] = box_color
        else:
            box_color = catid2color[region["type"]]
        box_layout = region["bbox"]
        draw_layout.rectangle(
            [(box_layout[0], box_layout[1]), (box_layout[2], box_layout[3])],
            outline=box_color,
            width=3,
        )

        if int(PIL.__version__.split(".")[0]) < 10:
            text_w, text_h = font.getsize(region["type"])
        else:
            left, top, right, bottom = font.getbbox(region["type"])
            text_w, text_h = right - left, bottom - top

        draw_layout.rectangle(
            [
                (box_layout[0], box_layout[1]),
                (box_layout[0] + text_w, box_layout[1] + text_h),
            ],
            fill=text_background_color,
        )
        draw_layout.text(
            (box_layout[0], box_layout[1]), region["type"], fill=text_color, font=font
        )

        if region["type"] == "table" or (
            region["type"] == "equation" and "latex" in region["res"]
        ):
            pass
        else:
            for text_result in region["res"]:
                boxes.append(np.array(text_result["text_region"]))
                txts.append(text_result["text"])
                scores.append(text_result["confidence"])

                if "text_word_region" in text_result:
                    for word_region in text_result["text_word_region"]:
                        char_box = word_region
                        box_height = int(
                            math.sqrt(
                                (char_box[0][0] - char_box[3][0]) ** 2
                                + (char_box[0][1] - char_box[3][1]) ** 2
                            )
                        )
                        box_width = int(
                            math.sqrt(
                                (char_box[0][0] - char_box[1][0]) ** 2
                                + (char_box[0][1] - char_box[1][1]) ** 2
                            )
                        )
                        if box_height == 0 or box_width == 0:
                            continue
                        boxes.append(word_region)
                        txts.append("")
                        scores.append(1.0)

    im_show = draw_ocr_box_txt(
        img_layout, boxes, txts, scores, font_path=font_path, drop_score=0
    )
    return im_show