def geom_name(self):
        "Return the Name of this Geometry."
        return capi.get_geom_name(self.ptr)