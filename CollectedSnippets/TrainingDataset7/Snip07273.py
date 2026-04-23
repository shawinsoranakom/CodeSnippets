def geom_typeid(self):
        "Return an integer representing the Geometry type."
        return capi.geos_typeid(self.ptr)