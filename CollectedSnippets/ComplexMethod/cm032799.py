def _extract_ocr_text(binary: bytes, meta_blocks: list[dict] | None = None) -> list[dict]:
    """
    Extract OCR text blocks using blackout strategy (with coordinate info).

    Strategy (ref: SmartResume):
    1. Render PDF pages to images
    2. Black out regions already extracted by metadata
    3. Run OCR on the blacked-out image, only recognizing content metadata missed
    4. Eliminates duplication at source, no IoU dedup needed downstream

    Args:
        binary: PDF file binary content
        meta_blocks: Text blocks from metadata extraction, used to black out existing text regions
    Returns:
        List of text blocks, each containing text, x0, top, x1, bottom, page fields
    """
    if meta_blocks is None:
        meta_blocks = []
    try:
        import pdfplumber
        from deepdoc.vision.ocr import OCR
        import numpy as np

        ocr = OCR()
        blocks = []

        with pdfplumber.open(BytesIO(binary)) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                # Render page to image (resolution=216 = 3x scale, since PDF default is 72 DPI)
                img = page.to_image(resolution=216)
                page_img = np.array(img.annotated)

                # Scale factor from PDF coordinates to image coordinates
                pdf_to_img_scale = 216.0 / 72.0  # = 3.0

                # Black out metadata-extracted text regions before OCR
                page_meta_blocks = [b for b in meta_blocks if b.get("page") == page_idx]
                if page_meta_blocks:
                    page_img = _blackout_text_regions(page_img, meta_blocks, page_idx, pdf_to_img_scale)

                ocr_result = ocr(page_img)
                if not ocr_result:
                    continue
                for box_info in ocr_result:
                    if isinstance(box_info, (list, tuple)) and len(box_info) >= 2:
                        coords = box_info[0]  # Coordinate points
                        text_info = box_info[1]
                        text = text_info[0] if isinstance(text_info, (list, tuple)) else str(text_info)
                        if text.strip() and isinstance(coords, (list, tuple)) and len(coords) >= 4:
                            # Extract bounding box from four corner points
                            xs = [p[0] for p in coords if isinstance(p, (list, tuple))]
                            ys = [p[1] for p in coords if isinstance(p, (list, tuple))]
                            if xs and ys:
                                blocks.append({
                                    "text": text.strip(),
                                    "x0": min(xs), "top": min(ys),
                                    "x1": max(xs), "bottom": max(ys),
                                    "page": page_idx,
                                })
        return blocks
    except Exception as e:
        logger.warning(f"OCR extraction failed: {e}")
        return []