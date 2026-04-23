def _apply_post_ocr(pdf_info_list, lang=None):
    need_ocr_list = []
    img_crop_list = []

    for page_info in pdf_info_list:
        for block in page_info.get('preproc_blocks', []):
            for span in _iter_block_spans(block):
                if 'np_img' in span:
                    need_ocr_list.append(span)
                    # Keep post-OCR rec aligned with the main OCR pipeline for vertical tall crops.
                    img_crop_list.append(rotate_vertical_crop_if_needed(span['np_img']))
                    span.pop('np_img')

        for block in page_info.get('discarded_blocks', []):
            for span in _iter_block_spans(block):
                if 'np_img' in span:
                    need_ocr_list.append(span)
                    # Keep post-OCR rec aligned with the main OCR pipeline for vertical tall crops.
                    img_crop_list.append(rotate_vertical_crop_if_needed(span['np_img']))
                    span.pop('np_img')

    if len(img_crop_list) == 0:
        return

    atom_model_manager = AtomModelSingleton()
    ocr_model = atom_model_manager.get_atom_model(
        atom_model_name='ocr',
        det_db_box_thresh=0.3,
        lang=lang
    )
    ocr_res_list = ocr_model.ocr(img_crop_list, det=False, tqdm_enable=True)[0]
    assert len(ocr_res_list) == len(
        need_ocr_list), f'ocr_res_list: {len(ocr_res_list)}, need_ocr_list: {len(need_ocr_list)}'
    for index, span in enumerate(need_ocr_list):
        ocr_text, ocr_score = ocr_res_list[index]
        if ocr_score > OcrConfidence.min_confidence:
            span['content'] = ocr_text
            span['score'] = float(f"{ocr_score:.3f}")
        else:
            span['content'] = ''
            span['score'] = 0.0