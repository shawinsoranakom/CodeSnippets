def srid(self):
        "Get the SRID for the geometry. Return None if no SRID is set."
        s = capi.geos_get_srid(self.ptr)
        if s == 0:
            return None
        else:
            return s