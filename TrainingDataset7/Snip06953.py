def point_count(self):
        "Return the number of Points in this Geometry."
        return capi.get_point_count(self.ptr)