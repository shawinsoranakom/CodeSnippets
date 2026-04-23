def jarvis_march(points: list[Point]) -> list[Point]:
    """
    Find the convex hull of a set of points using the Jarvis March algorithm.

    The algorithm starts with the leftmost point and wraps around the set of
    points, selecting the most counter-clockwise point at each step.

    Args:
        points: List of Point objects representing 2D coordinates

    Returns:
        List of Points that form the convex hull in counter-clockwise order.
        Returns empty list if there are fewer than 3 non-collinear points.
    """
    if len(points) <= 2:
        return []

    # Remove duplicate points to avoid infinite loops
    unique_points = list(set(points))

    if len(unique_points) <= 2:
        return []

    convex_hull: list[Point] = []

    # Find the leftmost point
    left_point_idx = _find_leftmost_point(unique_points)
    convex_hull.append(
        Point(unique_points[left_point_idx].x, unique_points[left_point_idx].y)
    )

    current_idx = left_point_idx
    while True:
        # Find the next counter-clockwise point
        next_idx = _find_next_hull_point(unique_points, current_idx)

        if next_idx == left_point_idx:
            break

        if next_idx == current_idx:
            break

        current_idx = next_idx
        _add_point_to_hull(convex_hull, unique_points[current_idx])

    # Check for degenerate cases
    if len(convex_hull) <= 2:
        return []

    # Check if last point is collinear with first and second-to-last
    last = len(convex_hull) - 1
    if _is_point_on_segment(convex_hull[last - 1], convex_hull[last], convex_hull[0]):
        convex_hull.pop()
        if len(convex_hull) == 2:
            return []

    # Verify the hull forms a valid polygon
    if not _is_valid_polygon(convex_hull):
        return []

    return convex_hull