def graham_scan(points: Sequence[Point]) -> list[Point]:
    """
    Find the convex hull of a set of points using the Graham scan algorithm.

    The algorithm works as follows:
    1. Find the bottom-most point (or left-most in case of tie)
    2. Sort all other points by polar angle with respect to the bottom-most point
    3. Process points in order, maintaining a stack of hull candidates
    4. Remove points that would create a clockwise turn

    Args:
        points: A sequence of Point objects

    Returns:
        A list of Point objects representing the convex hull in counter-clockwise order.
        Returns an empty list if there are fewer than 3 distinct points or if all
        points are collinear.

    Time Complexity: O(n log n) due to sorting
    Space Complexity: O(n) for the output hull

    >>> graham_scan([])
    []
    >>> graham_scan([Point(0, 0)])
    []
    >>> graham_scan([Point(0, 0), Point(1, 1)])
    []
    >>> hull = graham_scan([Point(0, 0), Point(1, 0), Point(0.5, 1)])
    >>> len(hull)
    3
    >>> Point(0, 0) in hull and Point(1, 0) in hull and Point(0.5, 1) in hull
    True
    """
    if len(points) <= 2:
        return []

    # Find the bottom-most point (left-most in case of tie)
    min_point = min(points)

    # Remove the min_point from the list
    points_list = [p for p in points if p != min_point]
    if not points_list:
        # Edge case where all points are the same
        return []

    def polar_angle_key(point: Point) -> tuple[float, float, float]:
        """
        Key function for sorting points by polar angle relative to min_point.

        Points are sorted counter-clockwise. When two points have the same angle,
        the farther point comes first (we'll remove duplicates later).
        """
        # We use a dummy third point (min_point itself) to calculate relative angles
        # Instead, we'll compute the angle between points
        dx = point.x - min_point.x
        dy = point.y - min_point.y

        # Use atan2 for angle, but we can also use cross product for comparison
        # For sorting, we compare orientations between consecutive points
        distance = min_point.euclidean_distance(point)
        return (dx, dy, -distance)  # Negative distance to sort farther points first

    # Sort by polar angle using a comparison based on cross product
    def compare_points(point_a: Point, point_b: Point) -> int:
        """Compare two points by polar angle relative to min_point."""
        orientation = min_point.consecutive_orientation(point_a, point_b)
        if orientation < 0.0:
            return 1  # point_a comes after point_b (clockwise)
        elif orientation > 0.0:
            return -1  # point_a comes before point_b (counter-clockwise)
        else:
            # Collinear: farther point should come first
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

    # Build the convex hull
    convex_hull: list[Point] = [min_point, points_list[0]]

    for point in points_list[1:]:
        # Skip consecutive points with the same angle (collinear with min_point)
        if min_point.consecutive_orientation(point, convex_hull[-1]) == 0.0:
            continue

        # Remove points that create a clockwise turn (or are collinear)
        while len(convex_hull) >= 2:
            orientation = convex_hull[-2].consecutive_orientation(
                convex_hull[-1], point
            )
            if orientation <= 0.0:
                convex_hull.pop()
            else:
                break

        convex_hull.append(point)

    # Need at least 3 points for a valid convex hull
    if len(convex_hull) <= 2:
        return []

    return convex_hull