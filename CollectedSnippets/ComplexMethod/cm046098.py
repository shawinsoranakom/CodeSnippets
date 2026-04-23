def get_high_image_coverage_ratio(sample_pdf_bytes, pages_to_check):
    pdf_stream = BytesIO(sample_pdf_bytes)
    parser = PDFParser(pdf_stream)
    document = PDFDocument(parser)

    if not document.is_extractable:
        return 1.0

    rsrcmgr = PDFResourceManager()
    laparams = LAParams(
        line_overlap=0.5,
        char_margin=2.0,
        line_margin=0.5,
        word_margin=0.1,
        boxes_flow=None,
        detect_vertical=False,
        all_texts=False,
    )
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    high_image_coverage_pages = 0
    page_count = 0

    for page in PDFPage.create_pages(document):
        if page_count >= pages_to_check:
            break

        interpreter.process_page(page)
        layout = device.get_result()

        page_width = layout.width
        page_height = layout.height
        page_area = page_width * page_height

        image_area = 0
        for element in layout:
            if isinstance(element, (LTImage, LTFigure)):
                img_width = element.width
                img_height = element.height
                image_area += img_width * img_height

        coverage_ratio = min(image_area / page_area, 1.0) if page_area > 0 else 0
        if coverage_ratio >= HIGH_IMAGE_COVERAGE_THRESHOLD:
            high_image_coverage_pages += 1

        page_count += 1

    pdf_stream.close()

    if page_count == 0:
        return 0.0

    return high_image_coverage_pages / page_count