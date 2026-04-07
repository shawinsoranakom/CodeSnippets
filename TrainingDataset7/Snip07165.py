def semi_major(self):
        "Return the Semi Major Axis for this Spatial Reference."
        return capi.semi_major(self.ptr, byref(c_int()))