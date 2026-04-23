def _build_indexed_text(blocks: list[dict]) -> tuple[str, list[str], list[dict]]:
    """

    Build indexed text with line numbers (ref: SmartResume Indexed Linearization)

    Merges sorted text blocks into lines and adds a unique index number to each line.
    Includes garbled line filtering logic and field label split repair.
    Also preserves coordinate info for each line, used for writing position_int etc. to chunks.

    Args:
        blocks: Sorted text block list
    Returns:
        (indexed_text, lines, line_positions) tuple:
        - indexed_text: Text string with line numbers
        - lines: Original line text list (without line numbers)
        - line_positions: Coordinate info for each line, format:
    """
    if not blocks:
        return "", [], []

    raw_lines = []
    raw_positions = []
    current_line_parts = []
    current_line_blocks = []
    current_top = blocks[0].get("top", 0)
    current_layoutno = blocks[0].get("layoutno", "")
    threshold = 10

    def _merge_line_position(line_blocks: list[dict]) -> dict:
        """Merge coordinates of all blocks in a line into outer bounding rectangle"""
        return {
            "page": line_blocks[0].get("page", 0),
            "x0": min(b.get("x0", 0) for b in line_blocks),
            "x1": max(b.get("x1", 0) for b in line_blocks),
            "top": min(b.get("top", 0) for b in line_blocks),
            "bottom": max(b.get("bottom", 0) for b in line_blocks),
        }

    for b in blocks:
        b_layoutno = b.get("layoutno", "")
        y_changed = abs(b.get("top", 0) - current_top) > threshold
        layout_changed = b_layoutno != current_layoutno and current_layoutno and b_layoutno
        if (y_changed or layout_changed) and current_line_parts:
            raw_lines.append(" ".join(current_line_parts))
            raw_positions.append(_merge_line_position(current_line_blocks))
            current_line_parts = []
            current_line_blocks = []
            current_top = b.get("top", 0)
            current_layoutno = b_layoutno
        current_line_parts.append(b["text"])
        current_line_blocks.append(b)

    if current_line_parts:
        raw_lines.append(" ".join(current_line_parts))
        raw_positions.append(_merge_line_position(current_line_blocks))

    # Filter empty and garbled lines (sync filter coordinates)
    lines = []
    line_positions = []
    for line, pos in zip(raw_lines, raw_positions):
        # Unicode normalization + long random string filtering (ref: SmartResume _clean_text_content)
        line = _clean_line_content(line)
        if not line:
            continue
        # Garbled detection: skip if valid chars (Chinese/ASCII letters/digits/common punctuation) ratio is too low
        if not _is_valid_line(line):
            continue
        lines.append(line)
        line_positions.append(pos)

    # Fix field label split issues
    # Coordinates are not affected, keep original positions
    lines = _fix_split_labels(lines)

    # Build indexed text with line numbers
    indexed_parts = [f"[{i}]: {line}" for i, line in enumerate(lines)]
    indexed_text = "\n".join(indexed_parts)

    return indexed_text, lines, line_positions