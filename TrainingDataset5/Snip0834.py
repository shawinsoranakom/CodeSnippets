def graham_scan(points: Sequence[Point]) -> list[Point]:
    if len(points) <= 2:
        return []

    min_point = min(points)

    points_list = [p for p in points if p != min_point]
    if not points_list:
        return []

    def polar_angle_key(point: Point) -> tuple[float, float, float]:
        dx = point.x - min_point.x
        dy = point.y - min_point.y

        distance = min_point.euclidean_distance(point)
        return (dx, dy, -distance)  
    def compare_points(point_a: Point, point_b: Point) -> int:
        orientation = min_point.consecutive_orientation(point_a, point_b)
        if orientation < 0.0:
            return 1 
        elif orientation > 0.0:
            return -1  
        else:
            dist_a = min_point.euclidean_distance(point_a)
            dist_b = min_point.euclidean_distance(point_b)
            if dist_b < dist_a:
                return -1
            elif dist_b > dist_a:
                return 1
            else:
                return 0

    from functools import cmp_to_key

    points_list.sort(key=cmp_to_key(compare_points))

    convex_hull: list[Point] = [min_point, points_list[0]]

    for point in points_list[1:]:
        if min_point.consecutive_orientation(point, convex_hull[-1]) == 0.0:
            continue

        while len(convex_hull) >= 2:
            orientation = convex_hull[-2].consecutive_orientation(
                convex_hull[-1], point
            )
            if orientation <= 0.0:
                convex_hull.pop()
            else:
                break

        convex_hull.append(point)

    if len(convex_hull) <= 2:
        return []

    return convex_hull
