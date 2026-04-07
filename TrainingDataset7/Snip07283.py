def ring(self):
        "Return whether or not the geometry is a ring."
        return capi.geos_isring(self.ptr)