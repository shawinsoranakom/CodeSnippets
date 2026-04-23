def _topology(self, gptr):
        "Return Geometry from the given pointer."
        return GEOSGeometry(gptr, srid=self.srid)