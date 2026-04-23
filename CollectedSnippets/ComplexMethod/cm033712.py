def find_gaps(
    from_data: IndexedPoints,
    from_index: list[str],
    to_data: IndexedPoints,
    target_indexes: TargetIndexes,
    only_exists: bool,
) -> IndexedPoints:
    """Find gaps in coverage between the from and to data sets."""
    target_data: IndexedPoints = {}

    for from_path, from_points in from_data.items():
        if only_exists and not os.path.isfile(to_bytes(from_path)):
            continue

        to_points = to_data.get(from_path, {})

        gaps = set(from_points.keys()) - set(to_points.keys())

        if gaps:
            gap_points = dict((key, value) for key, value in from_points.items() if key in gaps)
            target_data[from_path] = dict((gap, set(get_target_index(from_index[i], target_indexes) for i in indexes)) for gap, indexes in gap_points.items())

    return target_data