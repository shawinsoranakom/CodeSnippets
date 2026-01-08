def build_kdtree(points: list[list[float]], depth: int = 0) -> KDNode | None:
    if not points:
        return None

    k = len(points[0]) 
    axis = depth % k

    points.sort(key=lambda point: point[axis])
    median_idx = len(points) // 2

    left_points = points[:median_idx]
    right_points = points[median_idx + 1 :]

    return KDNode(
        point=points[median_idx],
        left=build_kdtree(left_points, depth + 1),
        right=build_kdtree(right_points, depth + 1),
    )
