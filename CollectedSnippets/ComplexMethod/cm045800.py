def _recursive_segment(
    entries: Sequence[_SortableEntry],
    prefer_horizontal_first: bool,
) -> list[_SortableEntry]:
    if len(entries) <= 1:
        return list(entries)

    horizontal_cut = _find_best_horizontal_cut_with_projection(entries)
    vertical_cut = _find_best_vertical_cut_with_projection(entries)

    has_valid_horizontal_cut = horizontal_cut.gap >= MIN_GAP_THRESHOLD
    has_valid_vertical_cut = vertical_cut.gap >= MIN_GAP_THRESHOLD

    if has_valid_horizontal_cut and has_valid_vertical_cut:
        use_horizontal_cut = horizontal_cut.gap > vertical_cut.gap
    elif has_valid_horizontal_cut:
        use_horizontal_cut = True
    elif has_valid_vertical_cut:
        use_horizontal_cut = False
    else:
        return _sort_by_y_then_x(entries)

    if use_horizontal_cut:
        groups = _split_by_horizontal_cut(entries, horizontal_cut.position)
    else:
        groups = _split_by_vertical_cut(entries, vertical_cut.position)

    if len(groups) <= 1:
        return _sort_by_y_then_x(entries)

    result: list[_SortableEntry] = []
    for group in groups:
        result.extend(_recursive_segment(group, prefer_horizontal_first))
    return result