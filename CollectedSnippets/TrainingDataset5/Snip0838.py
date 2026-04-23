def jarvis_march(points: list[Point]) -> list[Point]:
    if len(points) <= 2:
        return []

    unique_points = list(set(points))

    if len(unique_points) <= 2:
        return []

    convex_hull: list[Point] = []

    left_point_idx = _find_leftmost_point(unique_points)
    convex_hull.append(
        Point(unique_points[left_point_idx].x, unique_points[left_point_idx].y)
    )

    current_idx = left_point_idx
    while True:
        next_idx = _find_next_hull_point(unique_points, current_idx)

        if next_idx == left_point_idx:
            break

        if next_idx == current_idx:
            break

        current_idx = next_idx
        _add_point_to_hull(convex_hull, unique_points[current_idx])

    if len(convex_hull) <= 2:
        return []

    last = len(convex_hull) - 1
    if _is_point_on_segment(convex_hull[last - 1], convex_hull[last], convex_hull[0]):
        convex_hull.pop()
        if len(convex_hull) == 2:
            return []

    if not _is_valid_polygon(convex_hull):
        return []

    return convex_hull
