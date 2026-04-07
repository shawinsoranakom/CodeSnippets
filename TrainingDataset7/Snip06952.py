def geom_count(self):
        "Return the number of elements in this Geometry."
        return capi.get_geom_count(self.ptr)