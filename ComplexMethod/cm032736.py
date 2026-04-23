def _crop_pdf_preview(page_images, positions, zoom=PDF_PREVIEW_ZOOM):
    if not page_images or not positions:
        return None

    normalized_positions = []
    for pos in sorted(positions, key=lambda item: (item[0], item[3], item[1])):
        if len(pos) < 5:
            continue

        page_idx = int(pos[0]) - 1
        if not (0 <= page_idx < len(page_images)):
            continue

        left, right, top, bottom = map(float, pos[1:5])
        if right <= left or bottom <= top:
            continue
        normalized_positions.append((page_idx, left, right, top, bottom))

    if not normalized_positions:
        return None

    max_width = max(right - left for _, left, right, _, _ in normalized_positions)
    first_page, first_left, _, first_top, _ = normalized_positions[0]
    last_page, last_left, _, _, last_bottom = normalized_positions[-1]
    def page_height(idx):
        return page_images[idx].size[1] / zoom

    crop_positions = [
        (
            [first_page],
            first_left,
            first_left + max_width,
            max(0, first_top - PDF_PREVIEW_CONTEXT),
            max(first_top - PDF_PREVIEW_GAP, 0),
        )
    ]
    crop_positions.extend(
        [
            ([page_idx], left, right, top, bottom)
            for page_idx, left, right, top, bottom in normalized_positions
        ]
    )
    crop_positions.append(
        (
            [last_page],
            last_left,
            last_left + max_width,
            min(page_height(last_page), last_bottom + PDF_PREVIEW_GAP),
            min(page_height(last_page), last_bottom + PDF_PREVIEW_CONTEXT),
        )
    )

    imgs = []
    for idx, (pages, left, right, top, bottom) in enumerate(crop_positions):
        page_idx = pages[0]
        effective_right = (
            left + max_width if idx in {0, len(crop_positions) - 1} else max(left + 10, right)
        )
        imgs.append(
            page_images[page_idx].crop(
                (
                    left * zoom,
                    top * zoom,
                    effective_right * zoom,
                    min(bottom * zoom, page_images[page_idx].size[1]),
                )
            )
        )

    canvas_height = int(sum(img.size[1] for img in imgs) + PDF_PREVIEW_GAP * len(imgs))
    canvas_width = int(max(img.size[0] for img in imgs))
    preview = Image.new("RGB", (canvas_width, canvas_height), (245, 245, 245))

    height = 0
    for idx, img in enumerate(imgs):
        if idx in {0, len(imgs) - 1}:
            # Dim the extra context so the highlighted body stays visually distinct.
            img = img.convert("RGBA")
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            overlay.putalpha(128)
            img = Image.alpha_composite(img, overlay).convert("RGB")

        preview.paste(img, (0, height))
        height += img.size[1] + PDF_PREVIEW_GAP

    return preview