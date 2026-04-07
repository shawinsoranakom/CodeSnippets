def srid(self, srid):
        "Set the SRID for the geometry."
        capi.geos_set_srid(self.ptr, 0 if srid is None else srid)