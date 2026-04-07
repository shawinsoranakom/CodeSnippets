def from_gml(cls, gml_string):
        return cls(capi.from_gml(force_bytes(gml_string)))