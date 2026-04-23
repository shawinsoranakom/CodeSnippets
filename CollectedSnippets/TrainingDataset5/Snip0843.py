def digital_differential_analyzer_line(
    p1: tuple[int, int], p2: tuple[int, int]
) -> list[tuple[int, int]]:
    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1
    steps = max(abs(dx), abs(dy))
    x_increment = dx / float(steps)
    y_increment = dy / float(steps)
    coordinates = []
    x: float = x1
    y: float = y1
    for _ in range(steps):
        x += x_increment
        y += y_increment
        coordinates.append((round(x), round(y)))
    return coordinates
