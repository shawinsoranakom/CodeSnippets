def from_bbox(cls, bbox):
        "Construct a Polygon from a bounding box (4-tuple)."
        x0, y0, x1, y1 = bbox
        for z in bbox:
            if not isinstance(z, (float, int)):
                return GEOSGeometry(
                    "POLYGON((%s %s, %s %s, %s %s, %s %s, %s %s))"
                    % (x0, y0, x0, y1, x1, y1, x1, y0, x0, y0)
                )
        return Polygon(((x0, y0), (x0, y1), (x1, y1), (x1, y0), (x0, y0)))