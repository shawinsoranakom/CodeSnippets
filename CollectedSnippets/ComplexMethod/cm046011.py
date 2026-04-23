def _process_ocr_and_formulas(
    images_pil_list,
    model_list,
    language,
    inline_formula_enable,
    _ocr_enable,
    batch_ratio: int = 1,
):
    """处理OCR和公式识别"""

    # 遍历model_list,对文本块截图交由OCR识别
    # 根据_ocr_enable决定ocr只开det还是det+rec
    # 根据inline_formula_enable决定是使用mfd和ocr结合的方式,还是纯ocr方式

    # 将PIL图片转换为numpy数组
    np_images = [np.asarray(pil_image).copy() for pil_image in images_pil_list]

    # 获取混合模型实例
    hybrid_model_singleton = HybridModelSingleton()
    hybrid_pipeline_model = hybrid_model_singleton.get_model(
        lang=language,
        formula_enable=inline_formula_enable,
    )

    if inline_formula_enable:
        # 在进行`行内`公式检测和识别前，先将图像中的图片、表格、`行间`公式区域mask掉
        np_images = mask_image_regions(np_images, model_list)
        # 使用layout模型提供行内公式检测框
        images_layout_res = hybrid_pipeline_model.layout_model.batch_predict(
            np_images,
            batch_size=min(8, batch_ratio * LAYOUT_BASE_BATCH_SIZE),
        )
        images_mfd_res = _build_inline_formula_inputs(images_layout_res)
        # 公式识别
        inline_formula_list = hybrid_pipeline_model.mfr_model.batch_predict(
            images_mfd_res,
            np_images,
            batch_size=batch_ratio * MFR_BASE_BATCH_SIZE,
            interline_enable=True,
        )
    else:
        inline_formula_list = [[] for _ in range(len(images_pil_list))]

    mfd_res = []
    for page_inline_formula_list in inline_formula_list:
        page_mfd_res = []
        for formula in page_inline_formula_list:
            bbox = _formula_item_to_pixel_bbox(formula)
            if bbox is None:
                continue
            page_mfd_res.append({"bbox": bbox})
        mfd_res.append(page_mfd_res)

    # vlm没有执行ocr，需要ocr_det
    ocr_res_list = ocr_det(
        hybrid_pipeline_model,
        np_images,
        model_list,
        mfd_res,
        _ocr_enable,
        batch_ratio=batch_ratio,
    )

    # 如果需要ocr则做ocr_rec
    if _ocr_enable:
        need_ocr_list = []
        img_crop_list = []
        for page_ocr_res_list in ocr_res_list:
            for ocr_res in page_ocr_res_list:
                if 'np_img' in ocr_res:
                    need_ocr_list.append((page_ocr_res_list, ocr_res))
                    img_crop_list.append(ocr_res.pop('np_img'))
        if len(img_crop_list) > 0:
            # Process OCR
            ocr_result_list = hybrid_pipeline_model.ocr_model.ocr(img_crop_list, det=False, tqdm_enable=True)[0]

            # Verify we have matching counts
            assert len(ocr_result_list) == len(need_ocr_list), f'ocr_result_list: {len(ocr_result_list)}, need_ocr_list: {len(need_ocr_list)}'

            items_to_remove = []
            # Process OCR results for this language
            for index, (page_ocr_res_list, need_ocr_res) in enumerate(need_ocr_list):
                ocr_text, ocr_score = ocr_result_list[index]
                need_ocr_res['text'] = ocr_text
                need_ocr_res['score'] = float(f"{ocr_score:.3f}")
                should_remove = False
                if ocr_score < OcrConfidence.min_confidence:
                    should_remove = True
                else:
                    layout_res_bbox = need_ocr_res.get("bbox")
                    if layout_res_bbox is None and need_ocr_res.get("poly") is not None:
                        layout_res_bbox = [
                            need_ocr_res['poly'][0],
                            need_ocr_res['poly'][1],
                            need_ocr_res['poly'][4],
                            need_ocr_res['poly'][5],
                        ]
                    if layout_res_bbox is None:
                        should_remove = True
                        continue
                    layout_res_width = layout_res_bbox[2] - layout_res_bbox[0]
                    layout_res_height = layout_res_bbox[3] - layout_res_bbox[1]
                    if (
                            ocr_text in [
                                '（204号', '（20', '（2', '（2号', '（20号', '号','（204',
                                '(cid:)', '(ci:)', '(cd:1)', 'cd:)', 'c)', '(cd:)', 'c', 'id:)',
                                ':)', '√:)', '√i:)', '−i:)', '−:' , 'i:)',
                            ]
                            and ocr_score < 0.8
                            and layout_res_width < layout_res_height
                    ):
                        should_remove = True

                if should_remove:
                    items_to_remove.append((page_ocr_res_list, need_ocr_res))

            for page_ocr_res_list, need_ocr_res in items_to_remove:
                if need_ocr_res in page_ocr_res_list:
                    page_ocr_res_list.remove(need_ocr_res)

    _normalize_bbox(inline_formula_list, ocr_res_list, images_pil_list)
    merged_model_list = _merge_page_sidecar_items(
        model_list,
        inline_formula_list,
        ocr_res_list,
    )
    return merged_model_list, hybrid_pipeline_model