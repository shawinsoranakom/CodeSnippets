def convex_hull_melkman(points: list[Point]) -> list[Point]:
    points = sorted(_validate_input(points))
    n = len(points)

    convex_hull = points[:2]
    for i in range(2, n):
        det = _det(convex_hull[1], convex_hull[0], points[i])
        if det > 0:
            convex_hull.insert(0, points[i])
            break
        elif det < 0:
            convex_hull.append(points[i])
            break
        else:
            convex_hull[1] = points[i]
    i += 1

    for j in range(i, n):
        if (
            _det(convex_hull[0], convex_hull[-1], points[j]) > 0
            and _det(convex_hull[-1], convex_hull[0], points[1]) < 0
        ):
            continue

        convex_hull.insert(0, points[j])
        convex_hull.append(points[j])
        while _det(convex_hull[0], convex_hull[1], convex_hull[2]) >= 0:
            del convex_hull[1]
        while _det(convex_hull[-1], convex_hull[-2], convex_hull[-3]) <= 0:
            del convex_hull[-2]

    return sorted(convex_hull[1:] if len(convex_hull) > 3 else convex_hull)
