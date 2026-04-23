def clone(self):
        "Clone this Geometry."
        return GEOSGeometry(capi.geom_clone(self.ptr))