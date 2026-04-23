def doc_analyze_streaming(
        pdf_bytes_list,
        image_writer_list,
        lang_list,
        on_doc_ready,
        parse_method: str = 'auto',
        formula_enable=True,
        table_enable=True,
):
    if not (len(pdf_bytes_list) == len(image_writer_list) == len(lang_list)):
        raise ValueError("pdf_bytes_list, image_writer_list, and lang_list must have the same length")

    doc_contexts = []
    total_pages = 0
    for doc_index, (pdf_bytes, image_writer, lang) in enumerate(
        zip(pdf_bytes_list, image_writer_list, lang_list)
    ):
        _ocr_enable = _get_ocr_enable(pdf_bytes, parse_method)
        pdf_doc = open_pdfium_document(pdfium.PdfDocument, pdf_bytes)
        page_count = get_pdfium_document_page_count(pdf_doc)
        total_pages += page_count
        doc_contexts.append(
            {
                'doc_index': doc_index,
                'pdf_bytes': pdf_bytes,
                'pdf_doc': pdf_doc,
                'page_count': page_count,
                'next_page_idx': 0,
                'middle_json': init_middle_json(),
                'model_list': [],
                'image_writer': image_writer,
                'lang': lang,
                'ocr_enable': _ocr_enable,
                'closed': False,
            }
        )

    if total_pages == 0:
        _emit_zero_page_contexts(doc_contexts, on_doc_ready)
        return

    window_size = get_processing_window_size(default=64)
    total_batches = (total_pages + window_size - 1) // window_size
    logger.info(
        f'Pipeline processing-window multi-file run. doc_count={len(doc_contexts)}, '
        f'total_pages={total_pages}, window_size={window_size}, total_batches={total_batches}'
    )

    _emit_zero_page_contexts(doc_contexts, on_doc_ready)
    processed_pages = 0
    infer_start = time.time()
    try:
        progress_bar = None
        last_append_end_time = None
        try:
            batch_index = 0
            while processed_pages < total_pages:
                batch_index += 1
                batch_capacity = window_size
                batch_images = []
                batch_slices = []
                batch_payloads = []

                for context in doc_contexts:
                    if batch_capacity == 0:
                        break
                    page_start = context['next_page_idx']
                    if page_start >= context['page_count']:
                        continue
                    take_count = min(batch_capacity, context['page_count'] - page_start)
                    page_end = page_start + take_count - 1
                    images_list = load_images_from_pdf_doc(
                        context['pdf_doc'],
                        start_page_id=page_start,
                        end_page_id=page_end,
                        image_type=ImageType.PIL,
                        pdf_bytes=context['pdf_bytes'],
                    )
                    images_with_extra_info = [
                        (image_dict['img_pil'], context['ocr_enable'], context['lang'])
                        for image_dict in images_list
                    ]
                    batch_images.extend(images_with_extra_info)
                    batch_slices.append(
                        {
                            'doc_index': context['doc_index'],
                            'page_start': page_start,
                            'page_end': page_end,
                            'count': take_count,
                        }
                    )
                    batch_payloads.append((context, images_list, page_start, take_count))
                    context['next_page_idx'] = page_end + 1
                    batch_capacity -= take_count

                logger.info(
                    f'Pipeline processing window batch {batch_index}/{total_batches}: '
                    f'{processed_pages + len(batch_images)}/{total_pages} pages, '
                    f'batch_pages={len(batch_images)}, doc_slices={_format_doc_slices(batch_slices)}'
                )

                batch_results = batch_image_analyze(
                    batch_images,
                    formula_enable=formula_enable,
                    table_enable=table_enable,
                )
                if progress_bar is None:
                    progress_bar = tqdm(total=total_pages, desc="Processing pages")
                else:
                    exclude_progress_bar_idle_time(
                        progress_bar,
                        last_append_end_time,
                        now=time.time(),
                    )

                result_offset = 0
                for context, images_list, page_start, take_count in batch_payloads:
                    result_slice = batch_results[result_offset: result_offset + take_count]
                    append_batch_results_to_middle_json(
                        context['middle_json'],
                        result_slice,
                        images_list,
                        context['pdf_doc'],
                        context['image_writer'],
                        page_start_index=page_start,
                        ocr_enable=context['ocr_enable'],
                        model_list=context['model_list'],
                        progress_bar=progress_bar,
                    )
                    result_offset += take_count
                    _close_images(images_list)
                    images_list.clear()

                    if context['next_page_idx'] >= context['page_count'] and not context['closed']:
                        _finalize_processing_window_context(context, on_doc_ready)

                last_append_end_time = time.time()
                processed_pages += len(batch_images)
        finally:
            if progress_bar is not None:
                progress_bar.close()

        infer_time = round(time.time() - infer_start, 2)
        if infer_time > 0:
            logger.debug(
                f"processing-window multi-file infer finished, cost: {infer_time}, "
                f"speed: {round(total_pages / infer_time, 3)} page/s"
            )
    finally:
        for context in doc_contexts:
            if not context['closed']:
                close_pdfium_document(context['pdf_doc'])
                context['closed'] = True