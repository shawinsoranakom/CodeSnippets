def xml(self, dialect=""):
        "Return the XML representation of this Spatial Reference."
        return capi.to_xml(self.ptr, byref(c_char_p()), force_bytes(dialect))