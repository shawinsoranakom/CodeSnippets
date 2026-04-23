def read(self, wkb):
        "Return a GEOSGeometry for the given WKB buffer."
        return GEOSGeometry(super().read(wkb))