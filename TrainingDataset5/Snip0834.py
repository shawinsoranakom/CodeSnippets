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
