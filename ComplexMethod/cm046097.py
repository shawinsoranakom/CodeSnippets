def detect_cid_font_signal_pypdf(pdf_bytes, page_indices):
    reader = PdfReader(BytesIO(pdf_bytes))

    for page_index in page_indices:
        page = reader.pages[page_index]
        resources = _resolve_pdf_object(page.get("/Resources"))
        if not resources:
            continue

        fonts = _resolve_pdf_object(resources.get("/Font"))
        if not fonts:
            continue

        for _, font_ref in fonts.items():
            font = _resolve_pdf_object(font_ref)
            if not font:
                continue

            subtype = str(font.get("/Subtype"))
            encoding = str(font.get("/Encoding"))
            has_descendant_fonts = "/DescendantFonts" in font
            has_to_unicode = "/ToUnicode" in font

            if (
                subtype == "/Type0"
                and encoding in ("/Identity-H", "/Identity-V")
                and has_descendant_fonts
                and not has_to_unicode
            ):
                return True

    return False