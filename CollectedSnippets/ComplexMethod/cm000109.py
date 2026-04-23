def graham_scan(points: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Pure implementation of graham scan algorithm in Python

    :param points: The unique points on coordinates.
    :return: The points on convex hell.

    Examples:
    >>> graham_scan([(9, 6), (3, 1), (0, 0), (5, 5), (5, 2), (7, 0), (3, 3), (1, 4)])
    [(0, 0), (7, 0), (9, 6), (5, 5), (1, 4)]

    >>> graham_scan([(0, 0), (1, 0), (1, 1), (0, 1)])
    [(0, 0), (1, 0), (1, 1), (0, 1)]

    >>> graham_scan([(0, 0), (1, 1), (2, 2), (3, 3), (-1, 2)])
    [(0, 0), (1, 1), (2, 2), (3, 3), (-1, 2)]

    >>> graham_scan([(-100, 20), (99, 3), (1, 10000001), (5133186, -25), (-66, -4)])
    [(5133186, -25), (1, 10000001), (-100, 20), (-66, -4)]
    """

    if len(points) <= 2:
        # There is no convex hull
        raise ValueError("graham_scan: argument must contain more than 3 points.")
    if len(points) == 3:
        return points
    # find the lowest and the most left point
    minidx = 0
    miny, minx = maxsize, maxsize
    for i, point in enumerate(points):
        x = point[0]
        y = point[1]
        if y < miny:
            miny = y
            minx = x
            minidx = i
        if y == miny and x < minx:
            minx = x
            minidx = i

    # remove the lowest and the most left point from points for preparing for sort
    points.pop(minidx)

    sorted_points = sorted(points, key=lambda point: angle_comparer(point, minx, miny))
    # This insert actually costs complexity,
    # and you should instead add (minx, miny) into stack later.
    # I'm using insert just for easy understanding.
    sorted_points.insert(0, (minx, miny))

    stack: deque[tuple[int, int]] = deque()
    stack.append(sorted_points[0])
    stack.append(sorted_points[1])
    stack.append(sorted_points[2])
    # The first 3 points lines are towards the left because we sort them by their angle
    # from minx, miny.
    current_direction = Direction.left

    for i in range(3, len(sorted_points)):
        while True:
            starting = stack[-2]
            via = stack[-1]
            target = sorted_points[i]
            next_direction = check_direction(starting, via, target)

            if next_direction == Direction.left:
                current_direction = Direction.left
                break
            if next_direction == Direction.straight:
                if current_direction == Direction.left:
                    # We keep current_direction as left.
                    # Because if the straight line keeps as straight,
                    # we want to know if this straight line is towards left.
                    break
                elif current_direction == Direction.right:
                    # If the straight line is towards right,
                    # every previous points on that straight line is not convex hull.
                    stack.pop()
            if next_direction == Direction.right:
                stack.pop()
        stack.append(sorted_points[i])
    return list(stack)