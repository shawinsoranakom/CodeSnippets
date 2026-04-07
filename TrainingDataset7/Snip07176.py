def wkt(self):
        "Return the WKT representation of this Spatial Reference."
        return capi.to_wkt(self.ptr, byref(c_char_p()))