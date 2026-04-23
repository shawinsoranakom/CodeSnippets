def gml(self):
        "Return the GML representation of the Geometry."
        return capi.to_gml(self.ptr)