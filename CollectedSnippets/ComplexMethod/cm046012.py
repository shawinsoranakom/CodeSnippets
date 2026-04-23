def doc_analyze(
        pdf_bytes,
        image_writer: DataWriter | None,
        predictor: MinerUClient | None = None,
        backend="transformers",
        parse_method: str = 'auto',
        language: str = 'ch',
        inline_formula_enable: bool = True,
        model_path: str | None = None,
        server_url: str | None = None,
        **kwargs,
):
    if predictor is None:
        predictor = ModelSingleton().get_model(backend, model_path, server_url, **kwargs)
    predictor = _maybe_enable_serial_execution(predictor, backend)

    device = get_device()
    _ocr_enable = ocr_classify(pdf_bytes, parse_method=parse_method)
    _vlm_ocr_enable = _should_enable_vlm_ocr(_ocr_enable, language, inline_formula_enable)

    pdf_doc = open_pdfium_document(pdfium.PdfDocument, pdf_bytes)
    middle_json = init_middle_json(_ocr_enable, _vlm_ocr_enable)
    model_list = []
    doc_closed = False
    hybrid_pipeline_model = None
    try:
        page_count = get_pdfium_document_page_count(pdf_doc)
        configured_window_size = get_processing_window_size(default=64)
        effective_window_size = min(page_count, configured_window_size) if page_count else 0
        total_windows = (
            (page_count + effective_window_size - 1) // effective_window_size
            if effective_window_size
            else 0
        )
        logger.info(
            f'Hybrid processing-window run. page_count={page_count}, '
            f'window_size={configured_window_size}, total_windows={total_windows}'
        )

        batch_ratio = get_batch_ratio(device) if not _vlm_ocr_enable else 1

        infer_start = time.time()
        progress_bar = None
        last_append_end_time = None
        try:
            for window_index, window_start in enumerate(range(0, page_count, effective_window_size or 1)):
                window_end = min(page_count - 1, window_start + effective_window_size - 1)
                images_list = load_images_from_pdf_doc(
                    pdf_doc,
                    start_page_id=window_start,
                    end_page_id=window_end,
                    image_type=ImageType.PIL,
                    pdf_bytes=pdf_bytes,
                )
                try:
                    images_pil_list = [image_dict["img_pil"] for image_dict in images_list]
                    logger.info(
                        f'Hybrid processing window {window_index + 1}/{total_windows}: '
                        f'pages {window_start + 1}-{window_end + 1}/{page_count} '
                        f'({len(images_pil_list)} pages)'
                    )
                    if _vlm_ocr_enable:
                        with predictor_execution_guard(predictor):
                            window_model_list = predictor.batch_two_step_extract(images=images_pil_list)
                    else:
                        with predictor_execution_guard(predictor):
                            window_model_list = predictor.batch_two_step_extract(
                                images=images_pil_list,
                                not_extract_list=not_extract_list
                            )
                        window_model_list, hybrid_pipeline_model = _process_ocr_and_formulas(
                            images_pil_list,
                            window_model_list,
                            language,
                            inline_formula_enable,
                            _ocr_enable,
                            batch_ratio=batch_ratio,
                        )

                    model_list.extend(window_model_list)
                    if progress_bar is None:
                        progress_bar = tqdm(total=page_count, desc="Processing pages")
                    else:
                        exclude_progress_bar_idle_time(
                            progress_bar,
                            last_append_end_time,
                            now=time.time(),
                        )
                    append_page_model_list_to_middle_json(
                        middle_json,
                        window_model_list,
                        images_list,
                        pdf_doc,
                        image_writer,
                        page_start_index=window_start,
                        _ocr_enable=_ocr_enable,
                        _vlm_ocr_enable=_vlm_ocr_enable,
                        progress_bar=progress_bar,
                    )
                    last_append_end_time = time.time()
                finally:
                    _close_images(images_list)
        finally:
            if progress_bar is not None:
                progress_bar.close()

        infer_time = round(time.time() - infer_start, 2)
        if infer_time > 0 and page_count > 0:
            logger.debug(
                f"processing-window infer finished, cost: {infer_time}, "
                f"speed: {round(len(model_list) / infer_time, 3)} page/s"
            )

        finalize_middle_json(
            middle_json["pdf_info"],
            hybrid_pipeline_model,
            _ocr_enable,
            _vlm_ocr_enable,
        )
        close_pdfium_document(pdf_doc)
        doc_closed = True
        clean_memory(device)
        return middle_json, model_list, _vlm_ocr_enable
    finally:
        if not doc_closed:
            close_pdfium_document(pdf_doc)