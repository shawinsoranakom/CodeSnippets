def __init__(
        self,
        doc_orientation_classify_model_name=None,
        doc_orientation_classify_model_dir=None,
        doc_unwarping_model_name=None,
        doc_unwarping_model_dir=None,
        text_detection_model_name=None,
        text_detection_model_dir=None,
        textline_orientation_model_name=None,
        textline_orientation_model_dir=None,
        textline_orientation_batch_size=None,
        text_recognition_model_name=None,
        text_recognition_model_dir=None,
        text_recognition_batch_size=None,
        use_doc_orientation_classify=None,
        use_doc_unwarping=None,
        use_textline_orientation=None,
        text_det_limit_side_len=None,
        text_det_limit_type=None,
        text_det_thresh=None,
        text_det_box_thresh=None,
        text_det_unclip_ratio=None,
        text_det_input_shape=None,
        text_rec_score_thresh=None,
        return_word_box=None,
        text_rec_input_shape=None,
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

        params = {
            "doc_orientation_classify_model_name": doc_orientation_classify_model_name,
            "doc_orientation_classify_model_dir": doc_orientation_classify_model_dir,
            "doc_unwarping_model_name": doc_unwarping_model_name,
            "doc_unwarping_model_dir": doc_unwarping_model_dir,
            "text_detection_model_name": text_detection_model_name,
            "text_detection_model_dir": text_detection_model_dir,
            "textline_orientation_model_name": textline_orientation_model_name,
            "textline_orientation_model_dir": textline_orientation_model_dir,
            "textline_orientation_batch_size": textline_orientation_batch_size,
            "text_recognition_model_name": text_recognition_model_name,
            "text_recognition_model_dir": text_recognition_model_dir,
            "text_recognition_batch_size": text_recognition_batch_size,
            "use_doc_orientation_classify": use_doc_orientation_classify,
            "use_doc_unwarping": use_doc_unwarping,
            "use_textline_orientation": use_textline_orientation,
            "text_det_limit_side_len": text_det_limit_side_len,
            "text_det_limit_type": text_det_limit_type,
            "text_det_thresh": text_det_thresh,
            "text_det_box_thresh": text_det_box_thresh,
            "text_det_unclip_ratio": text_det_unclip_ratio,
            "text_det_input_shape": text_det_input_shape,
            "text_rec_score_thresh": text_rec_score_thresh,
            "return_word_box": return_word_box,
            "text_rec_input_shape": text_rec_input_shape,
        }
        base_params = {}
        for name, val in kwargs.items():
            if name in _DEPRECATED_PARAM_NAME_MAPPING:
                new_name = _DEPRECATED_PARAM_NAME_MAPPING[name]
                warn_deprecated_param(name, new_name)
                assert (
                    new_name in params
                ), f"{repr(new_name)} is not a valid parameter name."
                if params[new_name] is not None:
                    raise ValueError(
                        f"`{name}` and `{new_name}` are mutually exclusive."
                    )
                params[new_name] = val
            else:
                base_params[name] = val

        self._params = params

        super().__init__(**base_params)