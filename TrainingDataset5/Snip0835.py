def _find_leftmost_point(points: list[Point]) -> int:
    left_idx = 0
    for i in range(1, len(points)):
        if points[i].x < points[left_idx].x or (
            points[i].x == points[left_idx].x and points[i].y < points[left_idx].y
        ):
            left_idx = i
    return left_idx
