def pretty_wkt(self, simplify=0):
        "Return the 'pretty' representation of the WKT."
        return capi.to_pretty_wkt(self.ptr, byref(c_char_p()), simplify)