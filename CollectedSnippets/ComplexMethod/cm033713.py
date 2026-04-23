def find_missing(
    from_data: IndexedPoints,
    from_index: list[str],
    to_data: IndexedPoints,
    to_index: list[str],
    target_indexes: TargetIndexes,
    only_exists: bool,
) -> IndexedPoints:
    """Find coverage in from_data not present in to_data (arcs or lines)."""
    target_data: IndexedPoints = {}

    for from_path, from_points in from_data.items():
        if only_exists and not os.path.isfile(to_bytes(from_path)):
            continue

        to_points = to_data.get(from_path, {})

        for from_point, from_target_indexes in from_points.items():
            to_target_indexes = to_points.get(from_point, set())

            remaining_targets = set(from_index[i] for i in from_target_indexes) - set(to_index[i] for i in to_target_indexes)

            if remaining_targets:
                target_index = target_data.setdefault(from_path, {}).setdefault(from_point, set())
                target_index.update(get_target_index(name, target_indexes) for name in remaining_targets)

    return target_data