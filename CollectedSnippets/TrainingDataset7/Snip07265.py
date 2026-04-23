def __eq__(self, other):
        """
        Equivalence testing, a Geometry may be compared with another Geometry
        or an EWKT representation.
        """
        if isinstance(other, str):
            try:
                other = GEOSGeometry.from_ewkt(other)
            except (ValueError, GEOSException):
                return False
        return (
            isinstance(other, GEOSGeometry)
            and self.srid == other.srid
            and self.equals_exact(other)
        )