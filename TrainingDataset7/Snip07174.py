def import_wkt(self, wkt):
        "Import the Spatial Reference from OGC WKT (string)"
        capi.from_wkt(self.ptr, byref(c_char_p(force_bytes(wkt))))