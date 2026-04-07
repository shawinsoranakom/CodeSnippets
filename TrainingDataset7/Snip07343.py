def read(self, wkt):
        "Return a GEOSGeometry for the given WKT string."
        return GEOSGeometry(super().read(wkt))