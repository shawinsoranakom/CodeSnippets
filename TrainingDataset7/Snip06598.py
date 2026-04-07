def __init__(self, geom):
        """
        Oracle requires that polygon rings are in proper orientation. This
        affects spatial operations and an invalid orientation may cause
        failures. Correct orientations are:
         * Outer ring - counter clockwise
         * Inner ring(s) - clockwise
        """
        if isinstance(geom, Polygon):
            if self._polygon_must_be_fixed(geom):
                geom = self._fix_polygon(geom)
        elif isinstance(geom, GeometryCollection):
            if any(
                isinstance(g, Polygon) and self._polygon_must_be_fixed(g) for g in geom
            ):
                geom = self._fix_geometry_collection(geom)

        self.wkt = geom.wkt
        self.srid = geom.srid