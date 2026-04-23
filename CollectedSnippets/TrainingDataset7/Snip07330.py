def area(self):
        "Return the area of the Geometry."
        return capi.geos_area(self.ptr, byref(c_double()))