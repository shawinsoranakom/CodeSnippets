def _fix_polygon(cls, poly, clone=True):
        """Fix single polygon orientation as described in __init__()."""
        if clone:
            poly = poly.clone()

        if not poly.exterior_ring.is_counterclockwise:
            poly.exterior_ring = list(reversed(poly.exterior_ring))

        for i in range(1, len(poly)):
            if poly[i].is_counterclockwise:
                poly[i] = list(reversed(poly[i]))

        return poly