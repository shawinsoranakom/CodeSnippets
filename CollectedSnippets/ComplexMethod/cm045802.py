def _merge_cross_layout_elements(
    sorted_main: Sequence[_SortableEntry],
    cross_layout_entries: Sequence[_SortableEntry],
) -> list[_SortableEntry]:
    if not cross_layout_entries:
        return list(sorted_main)

    if not sorted_main:
        return _sort_by_y_then_x(cross_layout_entries)

    sorted_cross_layout = _sort_by_y_then_x(cross_layout_entries)

    result: list[_SortableEntry] = []
    main_index = 0
    cross_index = 0

    while main_index < len(sorted_main) or cross_index < len(sorted_cross_layout):
        if cross_index >= len(sorted_cross_layout):
            result.append(sorted_main[main_index])
            main_index += 1
            continue

        if main_index >= len(sorted_main):
            result.append(sorted_cross_layout[cross_index])
            cross_index += 1
            continue

        main_entry = sorted_main[main_index]
        cross_entry = sorted_cross_layout[cross_index]
        if cross_entry.top <= main_entry.top:
            result.append(cross_entry)
            cross_index += 1
        else:
            result.append(main_entry)
            main_index += 1

    return result