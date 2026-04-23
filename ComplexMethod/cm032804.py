def _extract_description_from_range(
        index_range: list, lines: list[str],
        company: str = "", position: str = ""
) -> str:
    """
    Extract description from original text by index range (ref SmartResume's _extract_description_from_range).

    Key improvement:
    - Filter out lines containing both company name and position title (avoid mixing header lines into description)
    - Boundary safety checks

    Args:
        index_range: [start_line_number, end_line_number]
        lines: List of original line texts
        company: Company name (used to filter header lines)
        position: Position title (used to filter header lines)
    Returns:
        Extracted description text
    """
    if not index_range or len(index_range) != 2:
        return ""

    start_idx, end_idx = int(index_range[0]), int(index_range[1])

    # Boundary safety check
    if start_idx < 0 or end_idx >= len(lines) or start_idx > end_idx:
        return ""

    extracted_lines = lines[start_idx:end_idx + 1]

    # Filter out lines containing both company name and position title (ref SmartResume)
    if company or position:
        norm_company = _normalize_for_comparison(company)
        norm_position = _normalize_for_comparison(position)
        filtered = []
        for line in extracted_lines:
            norm_line = _normalize_for_comparison(line)
            # If a line contains both company name and position title, it's likely a header line, skip
            if norm_company and norm_position and norm_company in norm_line and norm_position in norm_line:
                continue
            # If a line exactly equals company name or position title, also skip
            if norm_line == norm_company or norm_line == norm_position:
                continue
            filtered.append(line)
        extracted_lines = filtered

    if not extracted_lines:
        return ""

    return "\n".join(line.strip() for line in extracted_lines if line.strip())