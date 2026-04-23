def fill_blank_rec(
        self,
        img: np.ndarray,
        sorted_polygons: np.ndarray,
        cell_box_map: Dict[int, List[str]],
    ) -> Dict[int, List[Any]]:
        """找到poly对应为空的框，尝试将直接将poly框直接送到识别中"""
        bgr_img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        img_crop_info_list = []
        img_crop_list = []
        for i in range(sorted_polygons.shape[0]):
            if cell_box_map.get(i):
                continue
            box = sorted_polygons[i]
            if self.ocr_engine is None:
                logger.warning(f"No OCR engine provided for box {i}: {box}")
                continue
            # 从img中截取对应的区域
            x1, y1, x2, y2 = int(box[0][0])+1, int(box[0][1])+1, int(box[2][0])-1, int(box[2][1])-1
            if x1 >= x2 or y1 >= y2 or x1 < 0 or y1 < 0:
                # logger.warning(f"Invalid box coordinates: {x1, y1, x2, y2}")
                continue
            # 判断长宽比
            if (x2 - x1) / (y2 - y1) > 20 or (y2 - y1) / (x2 - x1) > 20:
                # logger.warning(f"Box {i} has invalid aspect ratio: {x1, y1, x2, y2}")
                continue
            img_crop = bgr_img[int(y1):int(y2), int(x1):int(x2)]

            # 计算span的对比度，低于0.20的span不进行ocr
            if calculate_contrast(img_crop, img_mode='bgr') <= 0.17:
                cell_box_map[i] = [[box, "", 0.1]]
                # logger.debug(f"Box {i} skipped due to low contrast.")
                continue

            img_crop_list.append(img_crop)
            img_crop_info_list.append([i, box])

        if len(img_crop_list) > 0:
            # 进行ocr识别
            ocr_result = self.ocr_engine.ocr(img_crop_list, det=False)
            # ocr_result = [[]]
            # for crop_img in img_crop_list:
            #     tmp_ocr_result = self.ocr_engine.ocr(crop_img)
            #     if tmp_ocr_result[0] and len(tmp_ocr_result[0]) > 0 and isinstance(tmp_ocr_result[0], list) and len(tmp_ocr_result[0][0]) == 2:
            #         ocr_result[0].append(tmp_ocr_result[0][0][1])
            #     else:
            #         ocr_result[0].append(("", 0.0))

            if not ocr_result or not isinstance(ocr_result, list) or len(ocr_result) == 0:
                logger.warning("OCR engine returned no results or invalid result for image crops.")
                return cell_box_map
            ocr_res_list = ocr_result[0]
            if not isinstance(ocr_res_list, list) or len(ocr_res_list) != len(img_crop_list):
                logger.warning("OCR result list length does not match image crop list length.")
                return cell_box_map
            for j, ocr_res in enumerate(ocr_res_list):
                img_crop_info_list[j].append(ocr_res)

            for i, box, ocr_res in img_crop_info_list:
                # 处理ocr结果
                ocr_text, ocr_score = ocr_res
                # logger.debug(f"OCR result for box {i}: {ocr_text} with score {ocr_score}")
                if ocr_score < 0.6 or ocr_text in ['1','口','■','（204号', '（20', '（2', '（2号', '（20号', '号', '（204']:
                    # logger.warning(f"Low confidence OCR result for box {i}: {ocr_text} with score {ocr_score}")
                    box = sorted_polygons[i]
                    cell_box_map[i] = [[box, "", 0.1]]
                    continue
                cell_box_map[i] = [[box, ocr_text, ocr_score]]

        return cell_box_map