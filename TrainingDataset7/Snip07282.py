def hasm(self):
        "Return whether the geometry has a M dimension."
        if geos_version_tuple() < (3, 12):
            raise GEOSException("GEOSGeometry.hasm requires GEOS >= 3.12.0.")
        return capi.geos_hasm(self.ptr)