def __init__(
        self,
        layout_detection_model_name=None,
        layout_detection_model_dir=None,
        layout_threshold=None,
        layout_nms=None,
        layout_unclip_ratio=None,
        layout_merge_bboxes_mode=None,
        chart_recognition_model_name=None,
        chart_recognition_model_dir=None,
        chart_recognition_batch_size=None,
        region_detection_model_name=None,
        region_detection_model_dir=None,
        doc_orientation_classify_model_name=None,
        doc_orientation_classify_model_dir=None,
        doc_unwarping_model_name=None,
        doc_unwarping_model_dir=None,
        text_detection_model_name=None,
        text_detection_model_dir=None,
        text_det_limit_side_len=None,
        text_det_limit_type=None,
        text_det_thresh=None,
        text_det_box_thresh=None,
        text_det_unclip_ratio=None,
        textline_orientation_model_name=None,
        textline_orientation_model_dir=None,
        textline_orientation_batch_size=None,
        text_recognition_model_name=None,
        text_recognition_model_dir=None,
        text_recognition_batch_size=None,
        text_rec_score_thresh=None,
        table_classification_model_name=None,
        table_classification_model_dir=None,
        wired_table_structure_recognition_model_name=None,
        wired_table_structure_recognition_model_dir=None,
        wireless_table_structure_recognition_model_name=None,
        wireless_table_structure_recognition_model_dir=None,
        wired_table_cells_detection_model_name=None,
        wired_table_cells_detection_model_dir=None,
        wireless_table_cells_detection_model_name=None,
        wireless_table_cells_detection_model_dir=None,
        table_orientation_classify_model_name=None,
        table_orientation_classify_model_dir=None,
        seal_text_detection_model_name=None,
        seal_text_detection_model_dir=None,
        seal_det_limit_side_len=None,
        seal_det_limit_type=None,
        seal_det_thresh=None,
        seal_det_box_thresh=None,
        seal_det_unclip_ratio=None,
        seal_text_recognition_model_name=None,
        seal_text_recognition_model_dir=None,
        seal_text_recognition_batch_size=None,
        seal_rec_score_thresh=None,
        formula_recognition_model_name=None,
        formula_recognition_model_dir=None,
        formula_recognition_batch_size=None,
        use_doc_orientation_classify=None,
        use_doc_unwarping=None,
        use_textline_orientation=None,
        use_seal_recognition=None,
        use_table_recognition=None,
        use_formula_recognition=None,
        use_chart_recognition=None,
        use_region_detection=None,
        format_block_content=None,
        markdown_ignore_labels=None,
        lang=None,
        ocr_version=None,
        **kwargs,
    ):
        if ocr_version is not None and ocr_version not in _SUPPORTED_OCR_VERSIONS:
            raise ValueError(
                f"Invalid OCR version: {ocr_version}. Supported values are {_SUPPORTED_OCR_VERSIONS}."
            )

        if all(
            map(
                lambda p: p is None,
                (
                    text_detection_model_name,
                    text_detection_model_dir,
                    text_recognition_model_name,
                    text_recognition_model_dir,
                ),
            )
        ):
            if lang is not None or ocr_version is not None:
                det_model_name, rec_model_name = self._get_ocr_model_names(
                    lang, ocr_version
                )
                if det_model_name is None or rec_model_name is None:
                    raise ValueError(
                        f"No models are available for the language {repr(lang)} and OCR version {repr(ocr_version)}."
                    )
                text_detection_model_name = det_model_name
                text_recognition_model_name = rec_model_name
        else:
            if lang is not None or ocr_version is not None:
                warnings.warn(
                    "`lang` and `ocr_version` will be ignored when model names or model directories are not `None`.",
                    stacklevel=2,
                )
        params = locals().copy()
        params["text_detection_model_name"] = text_detection_model_name
        params["text_recognition_model_name"] = text_recognition_model_name
        params.pop("self")
        params.pop("kwargs")
        self._params = params

        super().__init__(**kwargs)