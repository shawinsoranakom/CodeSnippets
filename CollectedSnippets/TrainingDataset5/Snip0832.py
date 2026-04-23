def test_star_shape() -> None:
    p1 = Point(-5, 6)
    p2 = Point(-11, 0)
    p3 = Point(-9, -8)
    p4 = Point(4, 4)
    p5 = Point(6, -7)

    p6 = Point(-7, -2)
    p7 = Point(-2, -4)
    p8 = Point(0, 1)
    p9 = Point(1, 0)
    p10 = Point(-6, 1)

    hull_points = [p1, p2, p3, p4, p5]
    interior_points = [p6, p7, p8, p9, p10]
    all_points = hull_points + interior_points

    hull = graham_scan(all_points)

    for p in hull_points:
        assert p in hull

    for p in interior_points:
        assert p not in hull
