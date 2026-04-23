def valid(self):
        "Test the validity of this Geometry."
        return capi.geos_isvalid(self.ptr)