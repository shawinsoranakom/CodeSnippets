def _handle_empty_point(self, geom):
        from django.contrib.gis.geos import Point

        if isinstance(geom, Point) and geom.empty:
            if self.srid:
                # PostGIS uses POINT(NaN NaN) for WKB representation of empty
                # points. Use it for EWKB as it's a PostGIS specific format.
                # https://trac.osgeo.org/postgis/ticket/3181
                geom = Point(float("NaN"), float("NaN"), srid=geom.srid)
            else:
                raise ValueError("Empty point is not representable in WKB.")
        return geom