def _polygon_must_be_fixed(poly):
        return not poly.empty and (
            not poly.exterior_ring.is_counterclockwise
            or any(x.is_counterclockwise for x in poly)
        )