def geom_type(self):
        "Return a string representing the Geometry type, e.g. 'Polygon'"
        return capi.geos_type(self.ptr).decode()