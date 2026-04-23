def _calculate_bounding_region(
    entries: Sequence[_SortableEntry],
) -> tuple[float, float, float, float] | None:
    if not entries:
        return None

    left = min(entry.left for entry in entries)
    top = min(entry.top for entry in entries)
    right = max(entry.right for entry in entries)
    bottom = max(entry.bottom for entry in entries)
    if right <= left or bottom <= top:
        return None
    return (left, top, right, bottom)