def semi_minor(self):
        "Return the Semi Minor Axis for this Spatial Reference."
        return capi.semi_minor(self.ptr, byref(c_int()))