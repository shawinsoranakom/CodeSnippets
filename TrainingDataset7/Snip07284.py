def simple(self):
        "Return false if the Geometry isn't simple."
        return capi.geos_issimple(self.ptr)