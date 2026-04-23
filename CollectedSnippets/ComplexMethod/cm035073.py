def draw_ser_results(
    image, ocr_results, font_path="doc/fonts/simfang.ttf", font_size=14
):
    np.random.seed(2021)
    color = (
        np.random.permutation(range(255)),
        np.random.permutation(range(255)),
        np.random.permutation(range(255)),
    )
    color_map = {
        idx: (color[0][idx], color[1][idx], color[2][idx]) for idx in range(1, 255)
    }
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)
    elif isinstance(image, str) and os.path.isfile(image):
        image = Image.open(image).convert("RGB")
    img_new = image.copy()
    draw = ImageDraw.Draw(img_new)

    font = ImageFont.truetype(font_path, font_size, encoding="utf-8")
    for ocr_info in ocr_results:
        if ocr_info["pred_id"] not in color_map:
            continue
        color = color_map[ocr_info["pred_id"]]
        text = "{}: {}".format(ocr_info["pred"], ocr_info["transcription"])

        if "bbox" in ocr_info:
            # draw with ocr engine
            bbox = ocr_info["bbox"]
        else:
            # draw with ocr groundtruth
            bbox = trans_poly_to_bbox(ocr_info["points"])
        draw_box_txt(bbox, text, draw, font, font_size, color)

    img_new = Image.blend(image, img_new, 0.7)
    return np.array(img_new)