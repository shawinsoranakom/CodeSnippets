def _layout_aware_reorder(blocks: list[dict]) -> list[dict]:
    """
    Layout-aware hierarchical sorting (ref: SmartResume Hierarchical Re-ordering)

    Two-level sorting strategy:
    1. Inter-segment sorting: first by page number, then by Y coordinate (top to bottom), same row by X coordinate (left to right)
    2. Intra-segment sorting: within each logical segment, sort by reading order

    For multi-column resumes, detect column positions by clustering X coordinates,
    then sort by column order.

    Args:
        blocks: Text block list (with coordinate info)
    Returns:
        Sorted text block list
    """
    if not blocks:
        return blocks

    # Group by page
    pages = {}
    for b in blocks:
        pg = b.get("page", 0)
        pages.setdefault(pg, []).append(b)

    sorted_blocks = []
    for pg in sorted(pages.keys()):
        page_blocks = pages[pg]

        # Detect multi-column layout: by X coordinate median
        if len(page_blocks) > 5:
            x_centers = [(b["x0"] + b["x1"]) / 2 for b in page_blocks]
            x_min, x_max = min(x_centers), max(x_centers)
            page_width = x_max - x_min if x_max > x_min else 1

            # Simple two-column detection: if text blocks are clearly distributed on left and right sides
            mid_x = (x_min + x_max) / 2
            left_count = sum(1 for x in x_centers if x < mid_x - page_width * 0.1)
            right_count = sum(1 for x in x_centers if x > mid_x + page_width * 0.1)

            if left_count > 3 and right_count > 3:
                # Multi-column layout: left column first then right column, each column top to bottom
                left_blocks = [b for b in page_blocks if (b["x0"] + b["x1"]) / 2 < mid_x]
                right_blocks = [b for b in page_blocks if (b["x0"] + b["x1"]) / 2 >= mid_x]
                left_blocks.sort(key=lambda b: (b["top"], b["x0"]))
                right_blocks.sort(key=lambda b: (b["top"], b["x0"]))
                sorted_blocks.extend(left_blocks)
                sorted_blocks.extend(right_blocks)
                continue

        # Single-column layout: top to bottom, same row left to right
        page_blocks.sort(key=lambda b: (b["top"], b["x0"]))
        sorted_blocks.extend(page_blocks)

    return sorted_blocks