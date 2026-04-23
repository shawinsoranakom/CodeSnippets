def _find_best_vertical_cut_with_projection(
    entries: Sequence[_SortableEntry],
) -> _CutInfo:
    if len(entries) < 2:
        return _CutInfo(0.0, 0.0)

    edge_cut = _find_vertical_cut_by_edges(entries)
    if edge_cut.gap >= MIN_GAP_THRESHOLD:
        return edge_cut

    if len(entries) < 3:
        return edge_cut

    region = _calculate_bounding_region(entries)
    if region is None:
        return edge_cut

    region_width = region[2] - region[0]
    narrow_threshold = region_width * NARROW_ELEMENT_WIDTH_RATIO
    filtered_entries = [
        entry for entry in entries if entry.width >= narrow_threshold
    ]
    if len(filtered_entries) < 2 or len(filtered_entries) == len(entries):
        return edge_cut

    filtered_cut = _find_vertical_cut_by_edges(filtered_entries)
    if (
        filtered_cut.gap > edge_cut.gap
        and filtered_cut.gap >= MIN_GAP_THRESHOLD
    ):
        return filtered_cut
    return edge_cut