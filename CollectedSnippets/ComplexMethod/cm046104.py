def get_ocr_result_list(
    ocr_res,
    useful_list,
    ocr_enable,
    bgr_image,
    lang,
):
    paste_x, paste_y, xmin, ymin, xmax, ymax, new_width, new_height = useful_list
    ocr_result_list = []
    ori_im = bgr_image.copy()
    for box_ocr_res in ocr_res:
        img_crop = None
        need_ocr_rec = False

        if len(box_ocr_res) == 2:
            p1, p2, p3, p4 = box_ocr_res[0]
            text, score = box_ocr_res[1]
            # logger.info(f"text: {text}, score: {score}")
            if score < OcrConfidence.min_confidence:  # 过滤低置信度的结果
                continue
        else:
            p1, p2, p3, p4 = box_ocr_res
            text, score = "", 1

            if ocr_enable:
                tmp_box = copy.deepcopy(np.array([p1, p2, p3, p4]).astype('float32'))
                img_crop = get_rotate_crop_image_for_text_rec(ori_im, tmp_box)
                need_ocr_rec = True

        # average_angle_degrees = calculate_angle_degrees(box_ocr_res[0])
        # if average_angle_degrees > 0.5:
        poly = [p1, p2, p3, p4]

        if (p3[0] - p1[0]) < OcrConfidence.min_width:
            # logger.info(f"width too small: {p3[0] - p1[0]}, text: {text}")
            continue

        if calculate_is_angle(poly):
            # logger.info(f"average_angle_degrees: {average_angle_degrees}, text: {text}")
            # 与x轴的夹角超过0.5度，对边界做一下矫正
            # 计算几何中心
            x_center = sum(point[0] for point in poly) / 4
            y_center = sum(point[1] for point in poly) / 4
            new_height = ((p4[1] - p1[1]) + (p3[1] - p2[1])) / 2
            new_width = p3[0] - p1[0]
            p1 = [x_center - new_width / 2, y_center - new_height / 2]
            p2 = [x_center + new_width / 2, y_center - new_height / 2]
            p3 = [x_center + new_width / 2, y_center + new_height / 2]
            p4 = [x_center - new_width / 2, y_center + new_height / 2]

        # Convert the coordinates back to the original coordinate system
        p1 = [p1[0] - paste_x + xmin, p1[1] - paste_y + ymin]
        p2 = [p2[0] - paste_x + xmin, p2[1] - paste_y + ymin]
        p3 = [p3[0] - paste_x + xmin, p3[1] - paste_y + ymin]
        p4 = [p4[0] - paste_x + xmin, p4[1] - paste_y + ymin]

        bbox = normalize_to_int_bbox([p1, p2, p3, p4])
        if bbox is None:
            continue

        ocr_item = {
            "label": "ocr_text",
            "bbox": bbox,
            "score": 1.0 if ocr_enable else float(round(score, 2)),
            "text": text,
        }
        if need_ocr_rec:
            ocr_item["np_img"] = img_crop
            ocr_item["lang"] = lang
            ocr_item["_need_ocr_rec"] = True
        ocr_result_list.append(ocr_item)

    return ocr_result_list