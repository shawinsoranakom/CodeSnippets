def _construct_points(
    list_of_tuples: list[Point] | list[list[float]] | Iterable[list[float]],
) -> list[Point]:

    points: list[Point] = []
    if list_of_tuples:
        for p in list_of_tuples:
            if isinstance(p, Point):
                points.append(p)
            else:
                try:
                    points.append(Point(p[0], p[1]))
                except (IndexError, TypeError):
                    print(
                        f"Ignoring deformed point {p}. All points"
                        " must have at least 2 coordinates."
                    )
    return points
