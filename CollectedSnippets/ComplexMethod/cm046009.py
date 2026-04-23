def ocr_det(
    hybrid_pipeline_model,
    np_images,
    model_list,
    mfd_res,
    _ocr_enable,
    batch_ratio: int = 1,
):
    def _set_temp_pixel_bbox(res, pixel_bbox):
        res["_normalized_bbox"] = list(res["bbox"])
        res["bbox"] = pixel_bbox

    def _restore_normalized_bbox(res):
        normalized_bbox = res.pop("_normalized_bbox", None)
        if normalized_bbox is not None:
            res["bbox"] = normalized_bbox

    ocr_res_list = []
    if not hybrid_pipeline_model.enable_ocr_det_batch:
        # 非批处理模式 - 逐页处理
        for np_image, page_mfd_res, page_results in tqdm(
            zip(np_images, mfd_res, model_list),
            total=len(np_images),
            desc="OCR-det"
        ):
            ocr_res_list.append([])
            img_height, img_width = np_image.shape[:2]
            for res in page_results:
                if res['type'] not in not_extract_list:
                    continue
                x0 = max(0, int(res['bbox'][0] * img_width))
                y0 = max(0, int(res['bbox'][1] * img_height))
                x1 = min(img_width, int(res['bbox'][2] * img_width))
                y1 = min(img_height, int(res['bbox'][3] * img_height))
                if x1 <= x0 or y1 <= y0:
                    continue
                _set_temp_pixel_bbox(res, [x0, y0, x1, y1])
                try:
                    new_image, useful_list = crop_img(
                        res, np_image, crop_paste_x=50, crop_paste_y=50
                    )
                finally:
                    _restore_normalized_bbox(res)
                adjusted_mfdetrec_res = get_adjusted_mfdetrec_res(
                    page_mfd_res, useful_list
                )
                bgr_image = cv2.cvtColor(new_image, cv2.COLOR_RGB2BGR)
                ocr_res = hybrid_pipeline_model.ocr_model.ocr(
                    bgr_image, mfd_res=adjusted_mfdetrec_res, rec=False
                )[0]
                if ocr_res:
                    ocr_result_list = get_ocr_result_list(
                        ocr_res, useful_list, _ocr_enable, bgr_image, hybrid_pipeline_model.lang
                    )

                    ocr_res_list[-1].extend(ocr_result_list)
    else:
        # 批处理模式 - 按语言和分辨率分组
        # 收集所有需要OCR检测的裁剪图像
        all_cropped_images_info = []

        for np_image, page_mfd_res, page_results in zip(
                np_images, mfd_res, model_list
        ):
            ocr_res_list.append([])
            img_height, img_width = np_image.shape[:2]
            for res in page_results:
                if res['type'] not in not_extract_list:
                    continue
                x0 = max(0, int(res['bbox'][0] * img_width))
                y0 = max(0, int(res['bbox'][1] * img_height))
                x1 = min(img_width, int(res['bbox'][2] * img_width))
                y1 = min(img_height, int(res['bbox'][3] * img_height))
                if x1 <= x0 or y1 <= y0:
                    continue
                _set_temp_pixel_bbox(res, [x0, y0, x1, y1])
                try:
                    new_image, useful_list = crop_img(
                        res, np_image, crop_paste_x=50, crop_paste_y=50
                    )
                finally:
                    _restore_normalized_bbox(res)
                adjusted_mfdetrec_res = get_adjusted_mfdetrec_res(
                    page_mfd_res, useful_list
                )
                bgr_image = cv2.cvtColor(new_image, cv2.COLOR_RGB2BGR)
                all_cropped_images_info.append((
                    bgr_image, useful_list, adjusted_mfdetrec_res, ocr_res_list[-1]
                ))

        # 按分辨率分组并同时完成padding
        RESOLUTION_GROUP_STRIDE = 64  # 32

        resolution_groups = defaultdict(list)
        for crop_info in all_cropped_images_info:
            cropped_img = crop_info[0]
            h, w = cropped_img.shape[:2]
            # 直接计算目标尺寸并用作分组键
            target_h = ((h + RESOLUTION_GROUP_STRIDE - 1) // RESOLUTION_GROUP_STRIDE) * RESOLUTION_GROUP_STRIDE
            target_w = ((w + RESOLUTION_GROUP_STRIDE - 1) // RESOLUTION_GROUP_STRIDE) * RESOLUTION_GROUP_STRIDE
            group_key = (target_h, target_w)
            resolution_groups[group_key].append(crop_info)

        # 对每个分辨率组进行批处理
        for (target_h, target_w), group_crops in tqdm(resolution_groups.items(), desc=f"OCR-det"):
            # 对所有图像进行padding到统一尺寸
            batch_images = []
            for crop_info in group_crops:
                img = crop_info[0]
                h, w = img.shape[:2]
                # 创建目标尺寸的白色背景
                padded_img = np.ones((target_h, target_w, 3), dtype=np.uint8) * 255
                padded_img[:h, :w] = img
                batch_images.append(padded_img)

            # 批处理检测
            det_batch_size = min(len(batch_images), batch_ratio * OCR_DET_BASE_BATCH_SIZE)
            batch_results = hybrid_pipeline_model.ocr_model.text_detector.batch_predict(batch_images, det_batch_size)

            # 处理批处理结果
            for crop_info, (dt_boxes, _) in zip(group_crops, batch_results):
                bgr_image, useful_list, adjusted_mfdetrec_res, ocr_page_res_list = crop_info

                if dt_boxes is not None and len(dt_boxes) > 0:
                    # 处理检测框
                    dt_boxes_sorted = sorted_boxes(dt_boxes)
                    dt_boxes_merged = merge_det_boxes(dt_boxes_sorted) if dt_boxes_sorted else []

                    # 根据公式位置更新检测框
                    dt_boxes_final = (update_det_boxes(dt_boxes_merged, adjusted_mfdetrec_res)
                                      if dt_boxes_merged and adjusted_mfdetrec_res
                                      else dt_boxes_merged)

                    if dt_boxes_final:
                        ocr_res = [box.tolist() if hasattr(box, 'tolist') else box for box in dt_boxes_final]
                        ocr_result_list = get_ocr_result_list(
                            ocr_res, useful_list, _ocr_enable, bgr_image, hybrid_pipeline_model.lang
                        )
                        ocr_page_res_list.extend(ocr_result_list)
    return ocr_res_list