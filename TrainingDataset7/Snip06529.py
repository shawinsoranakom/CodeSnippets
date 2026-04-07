def __eq__(self, other):
        return (
            isinstance(other, WKTAdapter)
            and self.wkt == other.wkt
            and self.srid == other.srid
        )