def extract_pdf_positions(item):
    # Parser-owned canonical PDF coordinate shape:
    # [[page_number, left, right, top, bottom], ...]
    if not isinstance(item, dict):
        return []

    positions = _extract_raw_positions(item)
    ref_page_number = item.get("page_number")
    ref_page_number = int(ref_page_number) if isinstance(ref_page_number, (int, float)) else None
    if ref_page_number is not None and ref_page_number <= 0:
        ref_page_number += 1

    normalized_positions = []
    for pos in positions:
        if not isinstance(pos, (list, tuple)) or len(pos) < 5:
            continue

        page_number = pos[0][-1] if isinstance(pos[0], list) else pos[0]
        try:
            page_number = int(page_number)
            if ref_page_number is not None and page_number == ref_page_number - 1:
                page_number = ref_page_number
            elif page_number <= 0:
                page_number += 1

            normalized_positions.append(
                [page_number, float(pos[1]), float(pos[2]), float(pos[3]), float(pos[4])]
            )
        except (TypeError, ValueError):
            continue

    return normalized_positions