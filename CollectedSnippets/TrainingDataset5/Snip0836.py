def _find_next_hull_point(points: list[Point], current_idx: int) -> int:
    next_idx = (current_idx + 1) % len(points)
    while next_idx == current_idx:
        next_idx = (next_idx + 1) % len(points)

    for i in range(len(points)):
        if i == current_idx:
            continue
        cross = _cross_product(points[current_idx], points[i], points[next_idx])
        if cross > 0:
            next_idx = i

    return next_idx
