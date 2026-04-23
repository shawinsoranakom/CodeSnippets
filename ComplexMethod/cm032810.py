def _layout_detect_reorder(blocks: list[dict], binary: bytes) -> list[dict]:
    if not blocks:
        return blocks

    recognizer = _get_layout_recognizer()
    if recognizer is None:
        logger.info("Layout detector unavailable, falling back to heuristic sorting")
        return _layout_aware_reorder(blocks)

    try:
        import pdfplumber
        pages_blocks: dict[int, list[dict]] = {}
        for b in blocks:
            pg = b.get("page", 0)
            pages_blocks.setdefault(pg, []).append(b)

        page_indices = sorted(pages_blocks.keys())
        image_list = []
        ocr_res_per_page = []

        with pdfplumber.open(BytesIO(binary)) as pdf:
            for pg in page_indices:
                if pg >= len(pdf.pages):
                    continue
                page = pdf.pages[pg]
                pil_img = page.to_image(resolution=72 * 3).annotated
                image_list.append(pil_img)

                page_bxs = []
                for b in pages_blocks[pg]:
                    page_bxs.append({
                        "x0": float(b["x0"]),
                        "top": float(b["top"]),
                        "x1": float(b["x1"]),
                        "bottom": float(b["bottom"]),
                        "text": b["text"],
                        "page": pg,
                    })
                ocr_res_per_page.append(page_bxs)

        if not image_list:
            return _layout_aware_reorder(blocks)

        tagged_blocks, page_layouts = recognizer(
            image_list, ocr_res_per_page, scale_factor=3, thr=0.2, drop=False
        )

        if not tagged_blocks:
            logger.warning("Layout detector unavailable, falling back to heuristic sorting")
            return _layout_aware_reorder(blocks)

        tagged_per_page: dict[int, list[dict]] = {}
        for b in tagged_blocks:
            pg = b.get("page", 0)
            tagged_per_page.setdefault(pg, []).append(b)

        sorted_all = []
        total_layout_count = 0
        for pn, pg in enumerate(page_indices):
            page_bxs = tagged_per_page.get(pg, [])
            lts = page_layouts[pn] if pn < len(page_layouts) else []
            total_layout_count += len(lts)
            sorted_page = _resort_page_with_layout(page_bxs, lts)
            sorted_all.extend(sorted_page)

        for b in sorted_all:
            if "page" not in b:
                b["page"] = 0

        logger.info(f"YOLOv10 detector completed， {len(sorted_all)} total chunks，"
                    f"checked {total_layout_count} layout")
        return sorted_all

    except Exception as e:
        logger.warning(f"Layout detector unavailable, falling back to heuristic sorting: {e}")
        return _layout_aware_reorder(blocks)