def ocr(image_path: Path, prompt: str, ocr_detection: any, ocr_recognition: any, x: int, y: int) -> any:
    text_data = []
    coordinate = []
    image = Image.open(image_path)
    iw, ih = image.size

    image_full = cv2.imread(str(image_path))
    det_result = ocr_detection(image_full)
    det_result = det_result["polygons"]
    for i in range(det_result.shape[0]):
        pts = order_point(det_result[i])
        image_crop = crop_image(image_full, pts)
        result = ocr_recognition(image_crop)["text"][0]

        if result == prompt:
            box = [int(e) for e in list(pts.reshape(-1))]
            box = [box[0], box[1], box[4], box[5]]

            if calculate_size(box) > 0.05 * iw * ih:
                continue

            text_data.append(
                [
                    int(max(0, box[0] - 10) * x / iw),
                    int(max(0, box[1] - 10) * y / ih),
                    int(min(box[2] + 10, iw) * x / iw),
                    int(min(box[3] + 10, ih) * y / ih),
                ]
            )
            coordinate.append(
                [
                    int(max(0, box[0] - 300) * x / iw),
                    int(max(0, box[1] - 400) * y / ih),
                    int(min(box[2] + 300, iw) * x / iw),
                    int(min(box[3] + 400, ih) * y / ih),
                ]
            )

    max_length = 0
    if len(text_data) == 0:
        for i in range(det_result.shape[0]):
            pts = order_point(det_result[i])
            image_crop = crop_image(image_full, pts)
            result = ocr_recognition(image_crop)["text"][0]

            if len(result) < 0.3 * len(prompt):
                continue

            if result in prompt:
                now_length = len(result)
            else:
                now_length = longest_common_substring_length(result, prompt)

            if now_length > max_length:
                max_length = now_length
                box = [int(e) for e in list(pts.reshape(-1))]
                box = [box[0], box[1], box[4], box[5]]

                text_data = [
                    [
                        int(max(0, box[0] - 10) * x / iw),
                        int(max(0, box[1] - 10) * y / ih),
                        int(min(box[2] + 10, iw) * x / iw),
                        int(min(box[3] + 10, ih) * y / ih),
                    ]
                ]
                coordinate = [
                    [
                        int(max(0, box[0] - 300) * x / iw),
                        int(max(0, box[1] - 400) * y / ih),
                        int(min(box[2] + 300, iw) * x / iw),
                        int(min(box[3] + 400, ih) * y / ih),
                    ]
                ]

        if len(prompt) <= 10:
            if max_length >= 0.8 * len(prompt):
                return text_data, coordinate
            else:
                return [], []
        elif (len(prompt) > 10) and (len(prompt) <= 20):
            if max_length >= 0.5 * len(prompt):
                return text_data, coordinate
            else:
                return [], []
        else:
            if max_length >= 0.4 * len(prompt):
                return text_data, coordinate
            else:
                return [], []

    else:
        return text_data, coordinate