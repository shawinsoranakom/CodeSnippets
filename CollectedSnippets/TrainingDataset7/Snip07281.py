def hasz(self):
        "Return whether the geometry has a Z dimension."
        return capi.geos_hasz(self.ptr)