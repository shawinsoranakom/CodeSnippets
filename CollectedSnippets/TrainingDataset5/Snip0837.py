def _is_valid_polygon(hull: list[Point]) -> bool:
    for i in range(len(hull)):
        p1 = hull[i]
        p2 = hull[(i + 1) % len(hull)]
        p3 = hull[(i + 2) % len(hull)]
        if abs(_cross_product(p1, p2, p3)) > 1e-9:
            return True
    return False
