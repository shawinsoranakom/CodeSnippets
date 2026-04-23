def sort_entries(
    entries: Sequence[dict[str, Any]],
    *,
    beta: float = DEFAULT_BETA,
    density_threshold: float = DEFAULT_DENSITY_THRESHOLD,
) -> list[dict[str, Any]]:
    if len(entries) <= 1:
        return list(entries)

    valid_entries = _build_sortable_entries(entries)
    if len(valid_entries) <= 1:
        return [entry.payload for entry in valid_entries]

    cross_layout_entries = _identify_cross_layout_elements(valid_entries, beta)
    cross_layout_ids = {entry.index for entry in cross_layout_entries}
    remaining_entries = [
        entry for entry in valid_entries if entry.index not in cross_layout_ids
    ]

    if not remaining_entries:
        return [entry.payload for entry in _sort_by_y_then_x(valid_entries)]

    density_ratio = _compute_density_ratio(remaining_entries)
    prefer_horizontal_first = density_ratio > density_threshold
    sorted_main = _recursive_segment(remaining_entries, prefer_horizontal_first)
    merged_entries = _merge_cross_layout_elements(sorted_main, cross_layout_entries)
    return [entry.payload for entry in merged_entries]